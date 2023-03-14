from flask import Flask, g, render_template, request
import json
import pandas as pd
from pathlib import Path
import psycopg2
import os

app = Flask(__name__, static_url_path='/static')
HOST_NAME = os.getenv('HOST_NAME')
DB_NAME = os.getenv('DB_NAME')
USER_NAME = os.getenv('USER_NAME')
PW = os.getenv('PW')


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, params=None):
    conn = psycopg2.connect(
        host=HOST_NAME,
        database=DB_NAME,
        user=USER_NAME,
        password=PW
    )
    df = pd.read_sql_query(query, conn, params=params)
    return df


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


INT_RANGE_KEYS = ["credits", "health", "armor", "ult_points"]
STRING_LIST_KEYS = ["agent_name", "player_name", "gun"]


def search_for_agent_state_in_db_from_list(search_json_list, join_by_team=True):
    unique_cols = ['game_uuid', 'round_number', 'frames_since_round_start']
    if join_by_team:
        unique_cols.append('is_attacking')
    agent_state_df = None
    for agent_state_info in search_json_list:
        if agent_state_df is None:
            agent_state_df = search_for_agent_state_in_db(agent_state_info)
        else:
            agent_state_df = pd.merge(agent_state_df, search_for_agent_state_in_db(agent_state_info),
                                      on=unique_cols)
    return agent_state_df


def search_for_agent_state_in_db(search_json):
    where_conditions_list = []
    params = {}
    for key, value in search_json.items():
        if key in INT_RANGE_KEYS:
            where_conditions_list.append(f"{key} BETWEEN %({key}_min)s AND %({key}_max)s ")
            params[f"{key}_min"] = value[0]
            params[f"{key}_max"] = value[0]
        elif key in STRING_LIST_KEYS:
            where_conditions_list.append(f"{key} = ANY(%({key})s)")
            params[key] = value
    where_condition_string = f"WHERE {' AND '.join(where_conditions_list)}"

    state_count_min = 1
    state_count_max = 5
    if 'state_count' in search_json:
        state_count_min = search_json['state_count'][0]
        state_count_max = search_json['state_count'][1]
    params['state_count_min'] = state_count_min
    params['state_count_max'] = state_count_max

    cte = "WITH agent_state_select AS (SELECT round_number, frames_since_round_start, game_uuid, is_attacking, " \
          f"COUNT(*) as agent_state_count FROM agent_state {where_condition_string} " \
          "GROUP BY round_number, frames_since_round_start, game_uuid, is_attacking)" \
          "SELECT * FROM agent_state_select WHERE agent_state_count BETWEEN %(state_count_min)s AND %(state_count_max)s"
    agent_state_df = query_db(cte, params=params)
    agent_state_df.drop('agent_state_count', axis=1, inplace=True)
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
    agent_round_map_merge_df['round_start_embed_vod'] = \
        agent_round_map_merge_df.apply(create_embed_link, axis=1, args=('round_start_frame',))
    agent_round_map_merge_df['first_true_embed_vod'] = \
        agent_round_map_merge_df.apply(create_embed_link, axis=1, args=('first_true_frame_in_round',))
    agent_round_map_merge_df['last_true_embed_vod'] = \
        agent_round_map_merge_df.apply(create_embed_link, axis=1, args=('last_true_frame_in_round',))
    drop_cols = ['vod_link', 'vod_fps', 'round_start_frame', 'first_true_frame_in_round',
                 'last_true_frame_in_round']
    for col in drop_cols:
        agent_round_map_merge_df.drop(col, axis=1, inplace=True)
    return agent_round_map_merge_df


@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        json_data = json.loads(request.form.get('json_data'))
        agent_state_list = json_data['agent_state_list']
        agent_state_df = search_for_agent_state_in_db_from_list(agent_state_list)
        agent_state_df_dupe = agent_state_df
        if len(agent_state_df) == 0:
            return "NO RESULTS FOUND"
        else:
            unique_round_tuples = agent_state_df_dupe.drop_duplicates(subset=['game_uuid', 'round_number']) \
                [['game_uuid', 'round_number']].values.tolist()
            unique_round_str = str(unique_round_tuples).replace('[', '(').replace(']', ')')
            round_info_query = f"SELECT round_start_frame, round_number, attackers_won, game_uuid " \
                               f"FROM round_info WHERE (game_uuid, round_number) IN {unique_round_str}"
            round_info_df = query_db(round_info_query)

            map_list = agent_state_df['game_uuid'].tolist()
            map_round_str = ",".join(["'{}'".format(s.replace("'", "''")) for s in map_list])

            map_info_query = f"SELECT * " \
                             f"FROM map_info WHERE game_uuid IN ({map_round_str})"
            map_info_df = query_db(map_info_query)
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

            html_showable_df = convert_to_html_showable_df(agent_round_map_merge_df)
            col_skip = ['game_uuid', 'round_start_embed_vod', 'first_true_embed_vod', 'last_true_embed_vod']
            vod_links = ['round_start_embed_vod', 'first_true_embed_vod', 'last_true_embed_vod']

            return render_template('show_video.html', agent_state_table=html_showable_df,
                                   titles=agent_round_map_merge_df.columns.values, col_skip=col_skip,
                                   vod_links=vod_links)

    else:
        return render_template('json_input.html')


def get_rounds_map_df_by_uuid(game_uuid):
    game_uuid = str(game_uuid)
    rounds_query = "SELECT round_number, attackers_won, total_agent_events, round_start_frame," \
                   "        game_uuid " \
                   "FROM round_info WHERE game_uuid = %(game_uuid)s"
    params = {'game_uuid': game_uuid}
    rounds_df = query_db(rounds_query, params)

    map_query = "SELECT * FROM map_info WHERE game_uuid = %(game_uuid)s"
    map_df = query_db(map_query, params)
    return rounds_df, map_df


@app.route('/maps/<uuid:map_id>')
def map_page(map_id):
    # use the map_id to retrieve the necessary variables from your data source
    # ...
    rounds_df, map_df = get_rounds_map_df_by_uuid(map_id)
    round_map_df = rounds_df.merge(map_df, on='game_uuid')
    round_map_df['round_start_embed_vod'] = \
        round_map_df.apply(create_embed_link, axis=1, args=('round_start_frame',))
    round_map_df['round_winning_team'] = round_map_df.apply(add_winning_team_to_df, axis=1)
    vod_links = ['round_start_embed_vod']

    return render_template('map.html',
                           team_a=round_map_df.iloc[0]['first_half_attacking_team'],
                           team_b=round_map_df.iloc[0]['first_half_defending_team'],
                           date=round_map_df.iloc[0]['game_vod_time'],
                           map_name=round_map_df.iloc[0]['map_name'],
                           vod_links=vod_links,
                           rounds=round_map_df)


# @app.route('/data/', methods = ['POST', 'GET'])
# def data():
#     agent_html = get_dropdown_checkbox_html('agent')
#     gun_html = get_dropdown_checkbox_html('gun')
#     return render_template('test_form.html', agent_html=agent_html, gun_html=gun_html)
#     if request.method == 'GET':
#         return f"The URL /data is accessed directly. Try going to '/form' to submit form"
#     if request.method == 'POST':
#         form_data = request.form
#         json = form_data["json"]
#
#         df = query_db(f"SELECT round_number, game_id, frames_since_round_start, gun_count FROM guns_by_round "
#                       f"WHERE gun = '{gun}' AND gun_count > {count}")
#         game_ids = ','.join([str(x) for x in df['game_id'].unique().tolist()])
#         round_numbers = ','.join([str(x) for x in df['round_number'].unique().tolist()])
#
#         round_df = query_db(f"SELECT frames_since_vod_start, game_id, round_number FROM rounds "
#                             f"WHERE game_id IN ({game_ids}) AND round_number IN ({round_numbers})")
#         game_df = query_db(f"SELECT vod_link, game_id FROM games WHERE game_id IN ({game_ids})")
#         merged_df = round_df.merge(game_df, left_on='game_id', right_on='game_id')
#         merged_df = df.merge(merged_df, left_on=('game_id', 'round_number'), right_on=('game_id', 'round_number'))
#         merged_df['seconds_since_round_start'] = merged_df['frames_since_round_start'] // 60
#         merged_df['seconds_since_vod_start'] = merged_df['frames_since_vod_start'] // 60 \
#                                                + merged_df['seconds_since_round_start']
#         merged_df['seconds_since_vod_start'] = merged_df['seconds_since_vod_start'].astype(str)
#         merged_df['full_vod_link'] = merged_df[["vod_link", "seconds_since_vod_start"]].apply("?start=".join, axis=1)
#         return render_template('data.html',df = merged_df)


if __name__ == '__main__':
    app.run(port=1234)
