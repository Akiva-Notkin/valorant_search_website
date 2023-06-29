# Valorant Vod Searcher Overview
This README covers two main topics. 
First, it provides documentation on how to use the search tool. 
Second, it discusses the underlying data that powers this project.

## Search and how to use it
### Overview
This section is going to cover what searches there are and how to use them. 
All queries are in the form of a [JSON object](https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Objects/JSON).

### Search JSON Object
#### What is the Search JSON Object?
A Search JSON Object is the highest level JSON object that is used in the search queries. 

#### Search JSON Object Fields
Required fields: 

`agent_state_list`: List of  [Agent State JSON Objects](#AGENT STATE JSON OBJECT). 
The list of agent states to search for.

Optional fields:

`round_number`: Int_range. The round number of the query. Eg. `"round_number": [1, 5]` will query where the round number is 
between 1 and 5 inclusive.

`attackers_won`: Bool. True if the attackers won the round, false if the defenders won the round. 
Eg. `"attackers_won": true` will query for rounds where the attackers won.

`map_name`: String_list. The name of the map. Eg. `"map_name": ["bind", "haven"]` will query for maps on bind or haven.

`map_uuid`: String_list. The UUID of the map. Eg. `"map_uuid": ["e59aa87c-4574-4b5d-a9a1-54b5ff4d9c3c", 
"2c9d9c29-4274-4d8a-9c8b-78e963b9b8a4"]` will query for maps with the given UUIDs.

`first_half_attacking_team`: String_list. The team that was attacking in the first half. Eg. 
`"first_half_attacking_team": ["FCY", "GLAB"]` will query for maps where FCY or GLAB was attacking in the first half.

`first_half_defending_team`: String_list. The team that was defending in the first half. Eg. 
`"first_half_defending_team": ["FCY", "GLAB"]` will query for maps where FCY or GLAB was defending in the first half.

`seconds_into_round`: Int_range. The seconds into the round. Eg. `"seconds_into_round": [0, 30]` will query for agent 
states between 0 and 30 seconds into the round.

### Agent State JSON Object
#### What is the Agent State JSON Object?
An Agent State JSON Object is a JSON object that represents the state of an agent at a given time.

#### Agent State JSON Object Fields
Optional fields (at least one is required):

`agent_name`: String_list. The name of the agent. Eg. `"agent_name":["sage", "jett"]` will query for agent states where the agent is sage or jett.

`health`: Int_range. The health of the agent. Eg. `"health": [85, 95]` will query for agent states where the agent's health is between 85 and 95 inclusive.

`armor`: Int_range. The armor of the agent. Eg. `"armor": [85, 95]` will query for agent states where the agent's armor is between 85 and 95 inclusive.

`ult_points`: Int_range. The ult points of the agent. Note: If the agent has the ultimate it has 10 ult_points. 
Eg. `"ult_points": [4, 10]` will query for agent states where agent has at least 4 ult points, or has their ult.

`gun` String_list. The gun the agent has. Eg. `"gun": ["phantom", "vandal"]` will query for agent states where the agent has a phantom or a vandal.

`player_name`: String_list. The name of the player. 
Eg. `"player_name": ["HAVOC", "GUHRVN"]` will query for agent states where the player is HAVOC or GUHRVN.

`credits`: Int_range. The credits of the player. 
Eg. `"credits": [1000, 2000]` will query for agent states where the player has between 1000 and 2000 credits inclusive.

`c_util`: Int_range. The amount of util the player has in the "c" slot. Note: If the agent is "astra" this is the amount of stars they have.
Eg. `"c_util": [1, 1], agent_name: ["sage"]` will query for agent states where the player has exactly one "Barrier Orb".

`q_util`: Int_range. The amount of util the player has in the "q" slot. Note: If the agent is "astra" this is the amount of stars they have.
Eg. `"q_util": [1, 2], agent_name: ["sage"]` will query for agent states where the player has between one and two "Slow Orb"s, inclusive.

`e_util`: Int_range. The amount of util the player has in the "e" slot. Note: If the agent is "astra" this is the amount of stars they have.
Eg. `"e_util": [1, 1], agent_name: ["sage"]` will query for agent states where the player has exactly one "Healing Orb".

### Types of queries

#### Normal Query
`/normal` endpoint

The 'normal' query takes a [Search JSON Object](#SEARCH JSON OBJECT) and returns all VODs that match the query. 
The return formal

#### Versus Query
`/versus` endpoint

The 'versus' query takes two Search JSON Objects, Team 1 and Team 2, and returns all VODs where both teams are present. 
It also shows the round win counts for each of the two teams in rounds they played each other. This query is a bit more
experimental.

### Examples

#### Normal Query Examples

##### Example 1
```
{
  "agent_state_list": [{
    "agent_name": ["kayo"],
    "gun": ["phantom", "vandal"],
    "health": [46, 50],
    "ult_points": [5, 10]
  }]
}
```

This query would find all VODs where Kayo has a phantom or vandal, has between 46 and 50 health, 
and has at least 5 ult points, or has his ult.

##### Example 2
```
{
  "agent_state_list": [{
    "agent_name": ["kayo"],
    "gun": ["phantom", "vandal"],
    "health": [46, 50],
    "ult_points": [5, 10]
  }],
  "round_number": [1, 5],
  "attackers_won": true,
  "map_name": ["bind", "haven"],
  "first_half_attacking_team": ["FCY", "GLAB"],
  "first_half_defending_team": ["FCY", "GLAB"],
  "seconds_into_round": [0, 30]
}
```

This query would find all VODs where Kayo has a phantom or vandal, has between 46 and 50 health,
and has at least 5 ult points, or has his ult. The VODs must also be between round 1 and 5 inclusive,
the attackers must have won the round, the map must be bind or haven, the map UUID must be either
e59aa87c-4574-4b5d-a9a1-54b5ff4d9c3c or 2c9d9c29-4274-4d8a-9c8b-78e963b9b8a4, the first half attacking
team must be FCY or GLAB, the first half defending team must be FCY or GLAB, and the seconds into the
round must be between 0 and 30 inclusive.

##### Example 3
```
{
  "agent_state_list": [{
    "agent_name": ["sage"],
    "gun": ["phantom", "vandal"],
    "ult_points": [5, 10],
      "c_util": [1, 1],
      "q_util": [1, 2],
      "e_util": [1, 1]
  },
   {
    "agent_name": ["kayo"],
    "gun": ["phantom", "vandal"],
    "health": [46, 50],
    "ult_points": [5, 10]
  }],
}
```

This query would find all VODs with two distinct agent_states Sage has a phantom or vandal, has between 46 and 50 health,
and has at least 5 ult points, or has his ult. The VODs must also be between round 1 and 5 inclusive