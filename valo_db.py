#!/bin/python3
import os
import psycopg2
import pandas as pd

HOST_NAME = os.getenv('HOST_NAME')
DB_NAME = os.getenv('DB_NAME')
USER_NAME = os.getenv('USER_NAME')
PW = os.getenv('PW')

INT_RANGE_AGENT_KEYS = ["credits", "health", "armor", "ult_points", "c_util", "q_util", "e_util"]
STRING_LIST_AGENT_KEYS = ["agent_name", "player_name", "gun"]
BOOL_AGENT_KEYS = ["is_attacking"]

INT_RANGE_ROUND_KEYS = ["round_number", "frames_since_round_start"]
STRING_LIST_ROUND_KEYS = ["game_uuid"]
BOOL_ROUND_KEYS = ["attackers_won"]

INT_RANGE_MAP_KEYS = []
STRING_LIST_MAP_KEYS = ["map_name", "game_uuid"]
BOOL_MAP_KEYS = []


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
        """
        Gets agent state data from the database based on the search parameters
        :param dict search_json: A dictionary of search parameters
        :param bool join_by_team: Whether to join the agent_state table with the team table
        :return:
        """
        where_conditions_list = []
        params = {}
        for key, value in search_json.items():
            if key in INT_RANGE_AGENT_KEYS:
                where_conditions_list.append(f"{key} BETWEEN %({key}_min)s AND %({key}_max)s ")
                params[f"{key}_min"] = value[0]
                params[f"{key}_max"] = value[1]
            elif key in STRING_LIST_AGENT_KEYS:
                where_conditions_list.append(f"{key} = ANY(%({key})s)")
                params[key] = value
            elif key in BOOL_AGENT_KEYS:
                where_conditions_list.append(f"{key} = %({key})s")
                params[key] = value
        where_condition_string = f"WHERE {' AND '.join(where_conditions_list)}"
        if len(where_conditions_list) == 0:
            return None

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

    def get_filtered_rounds(self, json_data):
        """
        Gets a list of rounds that match the given filters
        :param dict json_data: A dictionary of filters
        :return: A dataframe of rounds that match the given filters
        :rtype: pd.DataFrame
        """
        where_conditions_list = []
        params = {}
        for key, value in json_data.items():
            if key in INT_RANGE_ROUND_KEYS:
                where_conditions_list.append(f"{key} BETWEEN %({key}_min)s AND %({key}_max)s ")
                params[f"{key}_min"] = value[0]
                params[f"{key}_max"] = value[1]
            elif key in STRING_LIST_ROUND_KEYS:
                where_conditions_list.append(f"{key} = ANY(%({key})s)")
                params[key] = value
            elif key in BOOL_ROUND_KEYS:
                where_conditions_list.append(f"{key} = %({key})s")
                params[key] = value
        if len(where_conditions_list) == 0:
            return None
        where_condition_string = f"WHERE {' AND '.join(where_conditions_list)}"
        round_info_query = f"SELECT round_start_frame, round_number, attackers_won, game_uuid " \
                           f"FROM round_info as ri {where_condition_string}"
        round_info_df = self.query_db(round_info_query, params=params)
        return round_info_df

    def get_filtered_maps(self, json_data):
        """
        Gets a list of maps that match the given filters
        :param dict json_data: A dictionary of filters
        :return: A dataframe of maps that match the given filters
        :rtype: pd.DataFrame
        """
        where_conditions_list = []
        params = {}
        for key, value in json_data.items():
            if key in INT_RANGE_MAP_KEYS:
                where_conditions_list.append(f"{key} BETWEEN %({key}_min)s AND %({key}_max)s ")
                params[f"{key}_min"] = value[0]
                params[f"{key}_max"] = value[1]
            elif key in STRING_LIST_MAP_KEYS:
                where_conditions_list.append(f"{key} = ANY(%({key})s)")
                params[key] = value
            elif key in BOOL_MAP_KEYS:
                where_conditions_list.append(f"{key} = %({key})s")
                params[key] = value
        where_condition_string = f"WHERE {' AND '.join(where_conditions_list)}"
        if len(where_conditions_list) == 0:
            return None
        map_info_query = f"SELECT * FROM map_info {where_condition_string}"
        map_info_df = self.query_db(map_info_query, params=params)
        return map_info_df

    def get_unique_rounds(self, agent_state_df):
        """
        Gets the unique rounds associated with an agent_state_df
        :param pd.DataFrame agent_state_df: The agent_state_df to get the unique rounds for
        :return: The unique rounds
        :rtype: pd.DataFrame
        """
        unique_round_tuples = agent_state_df.drop_duplicates(subset=['game_uuid', 'round_number']) \
            [['game_uuid', 'round_number']].values.tolist()
        unique_round_str = str(unique_round_tuples).replace('[', '(').replace(']', ')')
        round_info_query = f"SELECT round_start_frame, round_number, attackers_won, game_uuid " \
                           f"FROM round_info WHERE (game_uuid, round_number) IN {unique_round_str}"
        round_info_df = self.query_db(round_info_query)
        return round_info_df

    def get_unique_maps(self, agent_state_df):
        """
        Gets the unique maps associated with an agent_state_df
        :param pd.DataFrame agent_state_df: The agent_state_df to get the unique maps for
        :return: The unique maps
        :rtype: pd.DataFrame
        """
        unique_map_tuples = agent_state_df.drop_duplicates(subset=['game_uuid'])[['game_uuid']].values.tolist()
        unique_map_str = str(unique_map_tuples).replace('[', '(').replace(']', ')')
        map_info_query = f"SELECT * FROM map_info WHERE game_uuid IN {unique_map_str}"
        map_info_df = self.query_db(map_info_query)
        return map_info_df
