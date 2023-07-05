# Valorant Vod Searcher Overview
This README covers two main topics. 
First, it provides documentation on how to use the search tool.  
Second, it discusses the underlying data that powers this tool.

Link to the search tool: https://valorantvodsearch.com

## Search and how to use it
### Overview
This section is going to cover what searches there are and how to use them. 
All queries are in the form of a [JSON object](https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Objects/JSON). Construct the JSON object, put it into the text
boxes for the page, then hit submit. Thats currently the only way to search the data.

### Search JSON Object
#### What is the Search JSON Object?
A Search JSON Object is the highest level JSON object that is used in the search queries. 

#### Search JSON Object Fields
Required fields: 

`agent_state_list`: List of  [Agent State JSON Objects](https://github.com/Akiva-Notkin/valorant_search_website#agent-state-json-object). 
The list of agent states to search for.

Optional fields:

`round_number`: Int_range. The round number of the query. Eg. `"round_number": [1, 5]` will query where the round number is 
between 1 and 5 inclusive.

`attackers_won`: Bool. True if the attackers won the round, false if the defenders won the round. 
Eg. `"attackers_won": true` will query for rounds where the attackers won.

`map_name`: String_list. The name of the map. Eg. `"map_name": ["bind", "haven"]` will query for maps on bind or haven.

`game_uuid`: String_list. The UUID of the game. Eg. `"map_uuid": ["e59aa87c-4574-4b5d-a9a1-54b5ff4d9c3c", 
"2c9d9c29-4274-4d8a-9c8b-78e963b9b8a4"]` will query for maps with the given UUIDs.

`first_half_attacking_team`: String_list. The team that was attacking in the first half. Eg. 
`"first_half_attacking_team": ["FCY", "GLAB"]` will query for maps where FCY or GLAB was attacking in the first half.

`first_half_defending_team`: String_list. The team that was defending in the first half. Eg. 
`"first_half_defending_team": ["FCY", "GLAB"]` will query for maps where FCY or GLAB was defending in the first half.

`seconds_into_round`: Int_range. The seconds into the round. Eg. `"seconds_into_round": [0, 30]` will query for agent 
states between 0 and 30 seconds into the round.

### Agent State JSON Object
#### What is the Agent State JSON Object?
An Agent State JSON Object is a JSON object that represents the state of an agent at a given time. The [Search JSON Object](https://github.com/Akiva-Notkin/valorant_search_website#agent-state-json-object)
must include a list of Agent State JSON Objects. 

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

`is_attacking`: Bool. True if the agent is attacking, false if the agent is defending. 
Eg. `"is_attacking": true` will query for agent states where the agent is attacking.

`credits`: Int_range. The credits of the player. 
Eg. `"credits": [1000, 2000]` will query for agent states where the player has between 1000 and 2000 credits inclusive.

`c_util`: Int_range. The amount of util the player has in the "c" slot. Note: If the agent is "astra" this is the amount of stars they have.
Eg. `"c_util": [1, 1], agent_name: ["sage"]` will query for agent states where the player has exactly one "Barrier Orb".

`q_util`: Int_range. The amount of util the player has in the "q" slot. Note: If the agent is "astra" this is the amount of stars they have.
Eg. `"q_util": [1, 2], agent_name: ["sage"]` will query for agent states where the player has between one and two "Slow Orb"s, inclusive.

`e_util`: Int_range. The amount of util the player has in the "e" slot. Note: If the agent is "astra" this is the amount of stars they have.
Eg. `"e_util": [1, 1], agent_name: ["sage"]` will query for agent states where the player has exactly one "Healing Orb".

`state_count`: Int_range. The amount of times this state should be true in the frame. 
Eg. `"state_count": [1, 1], "gun": ["phantom"]` will query for agent states where there is exactly one phantom in the frame

### Types of queries

#### Normal Query
`/normal` endpoint

The 'normal' query takes a [Search JSON Object](https://github.com/Akiva-Notkin/valorant_search_website#agent-state-json-object) and returns all VODs that match the query. 
The return formal

#### Versus Query
`/versus` endpoint

The 'versus' query takes two [Search JSON Object](https://github.com/Akiva-Notkin/valorant_search_website#agent-state-json-object), Team 1 and Team 2, and returns all VODs where both teams are present. 
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
and has at least 5 ult points, or has his ult. The VODs must also be between round 1 and 5 inclusive.

## Data Discussion
### List of scraped events
Below is a list of the events scraped for the underlying data. If you have VODs from this time period that are not on the list, please reach out with links and I can add them to the data set.

- VCT Champions 2022
- VCT LOCK//IN
- VCT Game Changers Championship 2022
- VCT Game Changers BR 
- VCT Game Changers KR 2022 (September 22,23)
- VCT Challengers SEA VN 2023 Split 1
- VCT Challengers SEA TH 2023 Split 1
- VCT Challengers SEA PH 2023 Split 1
- VCT Challengers SEA ID 2023 Split 1
- VCT Challengers BR 2023 Split 1


### Data quality Overview
This section is going to discuss the underlying data of the search tool. 
Most of this section is going to be a discussion of data quality, both in terms of where it is now, 
and also where (and how) I think data quality can be improved. 

Below is a table which shows the approximate accuracy for each agent_state field.
It was calculated on a set of 110 frames from 20 VODs. This accuracy is calculated by the amount of times the field was
guessed correctly, divided by the total number of guesses. So for example, if there are two agents, one with a `phantom`
and one with a `vandal` if I guess both are `phantom` then I have a .5 accuracy for the `gun` field.

| Field | Accuracy |
| --- | --- |
| health | 0.9926739926739927 |
| agent_name | 0.9963369963369964 |
| player_name | 0.9133089133089133 |
| armor | 0.8644688644688645 |
| gun | 0.960927960927961 |
| credits | 0.8754578754578755 |
| ult_points | 1.0 |
| util | 0.9951159951159951 |

This shows that most frames have something incorrectly labeled. So when you construct very detailed queries, 
its very unlikely to find something that exactly matches, because the data is not perfect.

### Data quality by field
Now I'm going to go field by field discussing the quality of the data, and how it can be improved (if at all). 

#### Health
The health field is very accurate currently. The only way I know to improve it is to throw a stupid amount of money at it. 
I'm talking like 100x the unit price of analyzing a VOD. I don't think that would guarantee 100% accuracy anyway. So this is probably
about what you should expect for health accuracy.

#### Agent Name
Here are more detailed states on the agent name field. It was calculated in the same way as the table above.

| Agent | Accuracy |
| --- | --- |
| cypher | 1.0 |
| raze | 1.0 |
| brimstone | 0.9655172413793104 |
| sova | 1.0 |
| jett | 1.0 |
| sage | 1.0 |
| viper | 1.0 |
| omen | 1.0 |
| killjoy | 1.0 |
| reyna | 1.0 |
| kayo | 0.989010989010989 |
| phoenix | 1.0 |
| breach | 1.0 |
| fade | 1.0 |
| astra | 1.0 |
| skye | 1.0 |
| chamber | 1.0 |
| neon | 1.0 |
| gekko | 0.0 |
| harbor | 1.0 |

Generally, this field is fairly accurate. Also this is one of the fields we have the most control over, 
so if we need to get it to a certain quality we should be able to. Basically it just takes more image classification. 
Its boring focused work, but it isnt super hard.

Note: I just realized that `yoru` isnt part of this testing set. Whoops. Also `gekko` was in like one frame and not 
part of the prediction data. Gekko is rare enough for this timeframe (he was released as an agent after most people stopped using the UI)
so I dont think it matters too much.

#### Gun
Here are more detailed states on the gun field. It was calculated in the same way as the table above.

| Gun | Accuracy |
| --- | --- |
| vandal | 0.9643916913946587 |
| operator | 0.9655172413793104 |
| marshal | 1.0 |
| sheriff | 0.971830985915493 |
| phantom | 0.9538461538461539 |
| spectre | 1.0 |
| stinger | 1.0 |
| bulldog | 1.0 |
| guardian | 1.0 |
| ghost | 0.8421052631578947 |
| frenzy | 1.0 |
| shorty | 0.875 |
| judge | 0.75 |
| odin | 1.0 |
| classic | 1.0 |

Of all the fields, this one is the one that is most likely to be improved. Similar to agent name, 
we have a lot of control over this field, so if we need to get it to a certain quality we should be able to. More classification work.

Note: This is also missing `bucky` and `ares`. `buckey` just isnt in the dataset at all. 
I just couldnt find examples of it so its not in the model. `ares` is the same problem as `yoru`, 
I just forgot to put it in the test set. Whoops again.

#### Player Name
This field isnt super accurate but honestly its better than I thought it would be. There are a few common issues, such
as numbers in names being converted to letters, such as `n1zzy` which the model will predict as `nizzy`. Similarly to health,
this could be solved by throwing more money at the problem, but I don't think its worth it.

Generally I would not use this field to search but I think it may be useful in the future to match up with other datasets.

#### Armor
This field I think can be improved but am less confident than other fields. The main issue is that there is an awkward
circle around the armor value which causes the model to see 0 way too often. There might be a way to scrub out that circle,
which would probably make the model more accurate. I tried once before, but it didnt seem like it was getting there. 
It deserves another shot though.

#### Credits
This field is pretty bad. It can probably be marginally improved, but I kinda suspect its not worth it. Credits are not
really relevant during a round, only between rounds so I feel that putting high effort into this field is not worth it.

#### Ult Points
Perfection. Not much to talk about here, it just works and I want to acknowledge that something just works.

#### Util
Almost perfect. The inaccuracies are in one specific place, which is `astra` utility. `astra` util accuracy is 
`0.88571428571`, all other agents are `1.0`.

The reason they're different is the UI for `astra` utility is very different form other utility. 
It has like 4 circles, instead of a number of dots. It probably can be improved, but I'm not sure by how much.

#### Other data quality issues
There are two other common data issues I want to talk about. Both have to do with the with what makes an agent "alive".
This causes two related but opposite issues. 
Sometimes when an agent is dead, the model will predict them as alive. 
Reversely, sometimes when an agent is alive, the model will predict them as dead.
I call them "extra_agents" and "missing_agents" respectively.

In the tests, out of 819 total agents in the test set, there were 3 extra agents and 4 missing agents. So both sub 1% 
but still not zero. I think this is a pretty good result, but it can for sure be improved upon.
