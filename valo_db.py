#!/bin/python3
import os
import psycopg2
import pandas as pd

HOST_NAME = os.getenv('HOST_NAME')
DB_NAME = os.getenv('DB_NAME')
USER_NAME = os.getenv('USER_NAME')
PW = os.getenv('PW')

INT_RANGE_KEYS = ["credits", "health", "armor", "ult_points", "c_util", "q_util", "e_util"]
STRING_LIST_KEYS = ["agent_name", "player_name", "gun"]


class ValoDatabase:
    def query_db(self, query, params=None):
        conn = psycopg2.connect(
            host=HOST_NAME,
            database=DB_NAME,
            user=USER_NAME,
            password=PW
        )
        df = pd.read_sql_query(query, conn, params=params)
        return df

    def search_for_agent_state_in_db(self, search_json, join_by_team=False):
        where_conditions_list = []
        params = {}
        for key, value in search_json.items():
            if key in INT_RANGE_KEYS:
                where_conditions_list.append(f"{key} BETWEEN %({key}_min)s AND %({key}_max)s ")
                params[f"{key}_min"] = value[0]
                params[f"{key}_max"] = value[1]
            elif key in STRING_LIST_KEYS:
                where_conditions_list.append(f"{key} = ANY(%({key})s)")
                params[key] = value
        where_condition_string = f"WHERE {' AND '.join(where_conditions_list)}"

        state_count_min = 1
        if join_by_team:
            state_count_max = 5
        else:
            state_count_max = 10
        if 'state_count' in search_json:
            state_count_min = search_json['state_count'][0]
            state_count_max = search_json['state_count'][1]
        params['state_count_min'] = state_count_min
        params['state_count_max'] = state_count_max

        cte = "WITH agent_state_select AS (SELECT round_number, frames_since_round_start, game_uuid" \
              f"{', is_attacking' if join_by_team else ''}, " \
              f"COUNT(*) as agent_state_count FROM agent_state {where_condition_string} " \
              "GROUP BY round_number, frames_since_round_start, game_uuid, is_attacking)" \
              "SELECT * FROM agent_state_select WHERE agent_state_count " \
              "BETWEEN %(state_count_min)s AND %(state_count_max)s"
        agent_state_df = self.query_db(cte, params=params)
        agent_state_df.drop('agent_state_count', axis=1, inplace=True)
        return agent_state_df

    def get_rounds_map_df_by_uuid(self, game_uuid):
        game_uuid = str(game_uuid)
        rounds_query = "SELECT round_number, attackers_won, total_agent_events, round_start_frame," \
                       "        game_uuid " \
                       "FROM round_info WHERE game_uuid = %(game_uuid)s"
        params = {'game_uuid': game_uuid}
        rounds_df = self.query_db(rounds_query, params)

        map_query = "SELECT * FROM map_info WHERE game_uuid = %(game_uuid)s"
        map_df = self.query_db(map_query, params)
        return rounds_df, map_df

    def get_unique_rounds(self, agent_state_df):
        unique_round_tuples = agent_state_df.drop_duplicates(subset=['game_uuid', 'round_number']) \
            [['game_uuid', 'round_number']].values.tolist()
        unique_round_str = str(unique_round_tuples).replace('[', '(').replace(']', ')')
        round_info_query = f"SELECT round_start_frame, round_number, attackers_won, game_uuid " \
                           f"FROM round_info WHERE (game_uuid, round_number) IN {unique_round_str}"
        round_info_df = self.query_db(round_info_query)
        return round_info_df

    def get_unique_maps(self, agent_state_df):
        unique_map_tuples = agent_state_df.drop_duplicates(subset=['game_uuid'])[['game_uuid']].values.tolist()
        unique_map_str = str(unique_map_tuples).replace('[', '(').replace(']', ')')
        map_info_query = f"SELECT * FROM map_info WHERE game_uuid IN {unique_map_str}"
        map_info_df = self.query_db(map_info_query)
        return map_info_df
