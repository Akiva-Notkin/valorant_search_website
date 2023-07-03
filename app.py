#!/bin/python3
from flask import Flask, g, render_template, request
import json
import pandas as pd
from pathlib import Path
from valo_db import ValoDatabase
from urllib.parse import quote_plus

app = Flask(__name__, static_url_path='/static')


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


valo_db = ValoDatabase()


@app.template_filter('urlencode')
def urlencode_filter(data):
    return quote_plus(data)


@app.template_filter('strip_spaces')
def strip_spaces(data):
    return data.strip()


def get_dropdown_checkbox_html(category_name, extension='webp'):
    folder_path = Path(f'static/{category_name}s')
    file_names = sorted([file.name.split(".")[0] for file in folder_path.iterdir() if file.is_file()])
    html = ''
    for value in file_names:
        if value.strip() != "":
            html += f'<input type="checkbox" id="{value}" ' \
                    f'onchange="checkboxStatusChange(\'{category_name}\')" ' \
                    f'value="{value}" />' \
                    f'<img src="static/{category_name}s/{value}.{extension}" / height="25"> ' \
                    f'{value}'
    return html


def search_for_agent_state_in_db_from_list(search_json_list, join_by_team=True):
    unique_cols = ['game_uuid', 'round_number', 'frames_since_round_start']
    if join_by_team:
        unique_cols.append('is_attacking')
    agent_state_df = None
    for agent_state_info in search_json_list:
        if agent_state_df is None:
            agent_state_df = valo_db.search_for_agent_state_in_db(agent_state_info, join_by_team=join_by_team)
        else:
            agent_state_df = pd.merge(agent_state_df, valo_db.search_for_agent_state_in_db(agent_state_info),
                                      on=unique_cols)
    return agent_state_df


def create_embed_link(row, start_frame_column):
    # Extract the video ID from the YouTube link
    video_id = row['vod_link'].split('=')[1]

    # Construct the base of the embed link
    embed_base = 'https://www.youtube.com/embed/{}?'.format(video_id)

    # If start_time is provided, add it to the embed link
    if row[start_frame_column]:
        embed_base += 'start={}&'.format(row[start_frame_column] // row['vod_fps'])

    # Add the remaining parameters to the embed link
    embed_link = embed_base + 'rel=0'

    return embed_link


def create_normal_link(row, start_frame_column):
    # Extract the video ID from the YouTube link
    video_id = row['vod_link'].split('=')[1]

    # Construct the base of the normal link
    link_base = 'https://www.youtube.com/watch?v={}'.format(video_id)

    # If start_time is provided, add it to the embed link
    if row[start_frame_column]:
        link_base += '&t={}'.format(row[start_frame_column] // row['vod_fps'])

    # Add the remaining parameters to the embed link
    full_link = link_base

    return full_link


def add_winning_team_to_df(row):
    if (1 <= row['round_number'] <= 12) or \
            (row['round_number'] > 24 and row['round_number'] % 2 != 0):
        if row['attackers_won']:
            return row['first_half_attacking_team']
        else:
            return row['first_half_defending_team']
    else:
        if row['attackers_won']:
            return row['first_half_defending_team']
        else:
            return row['first_half_attacking_team']


def convert_to_html_showable_df(agent_round_map_merge_df):
    agent_round_map_merge_df['Round Start'] = \
        agent_round_map_merge_df.apply(create_normal_link, axis=1, args=('round_start_frame',))
    agent_round_map_merge_df['First True'] = \
        agent_round_map_merge_df.apply(create_normal_link, axis=1, args=('first_true_frame_in_round',))
    agent_round_map_merge_df['Last True'] = \
        agent_round_map_merge_df.apply(create_normal_link, axis=1, args=('last_true_frame_in_round',))
    drop_cols = ['vod_link', 'vod_fps', 'round_start_frame', 'first_true_frame_in_round',
                 'last_true_frame_in_round']
    for col in drop_cols:
        agent_round_map_merge_df.drop(col, axis=1, inplace=True)
    return agent_round_map_merge_df


def get_agent_round_map_merge_df(json_data, join_by_team=False):
    if 'agent_state_list' not in json_data:
        return None, "No agent_state_list found in JSON data."
    agent_state_list = json_data['agent_state_list']
    agent_state_df = search_for_agent_state_in_db_from_list(agent_state_list, join_by_team=join_by_team)
    # rounds_df = search_for_rounds_from_json_data(json_data, join_by_team=join_by_team)
    if len(agent_state_df) == 0:
        return None, "Nothing found matching your query."
    else:

        round_info_df = valo_db.get_unique_rounds(agent_state_df)
        map_info_df = valo_db.get_unique_maps(agent_state_df)
        agent_round_merge_df = pd.merge(agent_state_df, round_info_df, on=('round_number', 'game_uuid'))
        agent_round_map_merge_df = pd.merge(agent_round_merge_df, map_info_df, on='game_uuid')
        agent_round_map_merge_df['first_true_frame_in_round'] = \
            agent_round_map_merge_df.groupby(['round_number', 'game_uuid'])[
                'frames_since_round_start'].transform('min') + agent_round_map_merge_df['round_start_frame']
        agent_round_map_merge_df['last_true_frame_in_round'] = \
            agent_round_map_merge_df.groupby(['round_number', 'game_uuid'])[
                'frames_since_round_start'].transform('max') + agent_round_map_merge_df['round_start_frame']
        agent_round_map_merge_df = agent_round_map_merge_df.drop('frames_since_round_start', axis=1)
        agent_round_map_merge_df = \
            agent_round_map_merge_df.groupby(['round_number', 'game_uuid'], as_index=False).agg(lambda x: x.iloc[0])
        return agent_round_map_merge_df, None


@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'GET':
        json_data = request.args.get('json_data', None)
        if json_data is None:
            return render_template('json_input.html', json_data=None)
        json_data = json.loads(json_data)
        return render_template('json_input.html', json_data=json_data)
    elif request.method == 'POST':
        json_data = json.loads(request.form.get('json_data'))
        agent_round_map_merge_df, comment = get_agent_round_map_merge_df(json_data, join_by_team=False)
        if agent_round_map_merge_df is None:
            return comment
        else:

            html_showable_df = convert_to_html_showable_df(agent_round_map_merge_df)
            col_skip = ['game_uuid', 'Round Start', 'First True', 'Last True']
            vod_links = ['Round Start', 'First True', 'Last True']

            return render_template('show_video.html', agent_state_table=html_showable_df,
                                   titles=agent_round_map_merge_df.columns.values, col_skip=col_skip,
                                   vod_links=vod_links, counts=[])

    else:
        return render_template('json_input.html')


@app.route('/versus', methods=['GET', 'POST'])
def versus_form():
    if request.method == 'GET':
        team_1_json_data = request.args.get('team_1_json_data', None)
        team_2_json_data = request.args.get('team_2_json_data', None)
        if team_1_json_data is None or team_2_json_data is None:
            return render_template('versus_input.html', team_1_json_data=None, team_2_json_data=None)
        team_1_json_data = json.loads(team_1_json_data)
        team_2_json_data = json.loads(team_2_json_data)
        return render_template('versus_input.html', team_1_json_data=team_1_json_data, team_2_json_data=team_2_json_data)
    if request.method == 'POST':
        team_1_json_data = json.loads(request.form.get('team_1_json_data'))
        team_2_json_data = json.loads(request.form.get('team_2_json_data'))
    else:
        return render_template('versus_input.html', team_1_json_data=None, team_2_json_data=None)

    team_1_agent_round_map_merge_df, comment = get_agent_round_map_merge_df(team_1_json_data, join_by_team=True)
    team_2_agent_round_map_merge_df, comment = get_agent_round_map_merge_df(team_2_json_data, join_by_team=True)
    if team_2_agent_round_map_merge_df is None or team_1_agent_round_map_merge_df is None:
        return comment
    else:
        # perform a cross join
        team_1_agent_round_map_merge_df['key'] = 1
        team_2_agent_round_map_merge_df['key'] = 1
        merged_df = pd.merge(team_1_agent_round_map_merge_df, team_2_agent_round_map_merge_df, on='key')

        # filter rows based on column matches and overlapping intervals
        merged_df = merged_df[
            (merged_df['game_uuid_x'] == merged_df['game_uuid_y']) &
            (merged_df['round_number_x'] == merged_df['round_number_y']) &
            (merged_df['is_attacking_x'] != merged_df['is_attacking_y']) &
            (merged_df['first_true_frame_in_round_x'] <= merged_df['last_true_frame_in_round_y']) &
            (merged_df['last_true_frame_in_round_x'] >= merged_df['first_true_frame_in_round_y'])
            ]

        team_2_agent_round_map_with_suffix = [f"{col}_y" for col in team_2_agent_round_map_merge_df.columns]

        # remove temporary columns from df2 and merged_df
        merged_df['first_true_frame_in_round'] = merged_df['first_true_frame_in_round_x'].where(
            merged_df['first_true_frame_in_round_x'] > merged_df['first_true_frame_in_round_y'],
            merged_df['first_true_frame_in_round_y'])
        merged_df['last_true_frame_in_round'] = merged_df['last_true_frame_in_round_x'].where(
            merged_df['last_true_frame_in_round_x'] < merged_df['last_true_frame_in_round_y'],
            merged_df['last_true_frame_in_round_y'])
        merged_df.drop(['key', 'last_true_frame_in_round_x', 'first_true_frame_in_round_x'], axis=1, inplace=True)
        merged_df = merged_df[[col for col in merged_df.columns if col not in team_2_agent_round_map_with_suffix]]
        merged_df.columns = merged_df.columns.str.rstrip('_x')
        merged_df['team_1_won_round'] = merged_df['is_attacking'] == merged_df['attackers_won']
        html_showable_df = convert_to_html_showable_df(merged_df)
        col_skip = ['game_uuid', 'Round Start', 'First True', 'Last True']
        vod_links = ['Round Start', 'First True', 'Last True']

        counts = {}

        if 'team_1_won_round' in merged_df:
            counts['true_count'] = merged_df['team_1_won_round'].value_counts().get(True, 0)
            counts['false_count'] = merged_df['team_1_won_round'].value_counts().get(False, 0)

        return render_template('show_video.html', agent_state_table=html_showable_df,
                               titles=merged_df.columns.values, col_skip=col_skip,
                               vod_links=vod_links, counts=counts)


@app.route('/maps/<uuid:map_id>')
def map_page(map_id):
    rounds_df, map_df = valo_db.get_rounds_map_df_by_uuid(map_id)
    round_map_df = rounds_df.merge(map_df, on='game_uuid')
    round_map_df['Round Start'] = \
        round_map_df.apply(create_embed_link, axis=1, args=('round_start_frame',))
    round_map_df['round_winning_team'] = round_map_df.apply(add_winning_team_to_df, axis=1)
    vod_links = ['Round Start']

    return render_template('map.html',
                           team_a=round_map_df.iloc[0]['first_half_attacking_team'],
                           team_b=round_map_df.iloc[0]['first_half_defending_team'],
                           date=round_map_df.iloc[0]['game_vod_time'],
                           map_name=round_map_df.iloc[0]['map_name'],
                           vod_links=vod_links,
                           rounds=round_map_df)


if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)
