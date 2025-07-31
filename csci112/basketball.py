
import pymongo
from pymongo import MongoClient
from pprint import pprint

MONGO_HOST = "172.31.27.133"
MONGO_PORT = 27017
MONGO_DB = "db"
connection = MongoClient(MONGO_HOST, MONGO_PORT)
db = connection[MONGO_DB]
basketball = db["basketball"]

# Our database allows us to query at different cardinalities: by player, role, team, game, season, or overall. It is also highly cusotmizable per requirements of the scout


# Average statistics per role
role = basketball.aggregate([
    {
        "$group": {"_id": "$position", "average points": {"$avg": "$player_stats.pts"}}
    },
    {
        "$project": {"_id": 0, "position": "$_id", "average points" : 1}
    }
])
pprint(list(role))


# Scouting for players in a position with a specific height and accuracy threshold
players = basketball.aggregate([
    {
        "$match": {
           "$and" : [{"position" : "center"}, {"height" : {"$gte" : 170}}, {"player_stats.3pt_pct" : {"$gte": 50}}]
        }
    },
    {
        "$group": {
            "_id": "$player_id", 
            "peakHeight": {"$max": "$height"}, 
            "average 3pt percentage": {"$avg": "$player_stats.3pt_pct"}, 
            "first_name": {"$first": "$first_name"}, 
            "last_name": {"$first": "$last_name"},
            "position": {"$first": "$position"}
        }
    }, # This of course assumes that the player's name will not change over time and that their height is either increasing or staying the same, no shrinking
    {
        "$project": {
            "_id": 0,
            "name": {"$concat": ["$first_name"," ","$last_name"]},
            "average 3pt percentage": 1,
            "height": "$peakHeight",
            "position": 1
        }
    }
])
pprint(list(players))

# We can zoom in further by looking at specific points of our player of interest, such as how often he gets injured throughout a season
injuries = basketball.aggregate([
    {
        "$match": {
            "$or": [{"$and": [{"first_name": "Eberhard"}, {"last_name": "Findon"}, {"season": 2017}, {"injury_diagnosis": {"$ne": ""}}]}, # can also search for specific injuries by replacing {"$ne": ""} with the injuries you want to check
                    {"$and": [{"first_name": "Elvyn"}, {"last_name": "Collop"}, {"season": 2017}, {"injury_diagnosis": {"$ne": ""}}]}
                    ]
        }
    },
        {
        "$group":{
            "_id": {"$concat": ["$first_name"," ","$last_name"]},
            "injury frequency": {"$sum": 1}
        }
    },
    {
        "$project": {"_id": 0, "name": "$_id", "injury frequency" : 1} 
    }
])
pprint(list(injuries))


# we can now move our focus to team performance, we first look at the list of teams then zero-in on desired stats
teams = basketball.distinct("team_id")
pprint(list(teams))

fouls = basketball.aggregate([
    {
        "$match": {
            "team_id" : "ADMU"
        }
    },
    {
        "$group":{
            "_id": "$team_id",
            "average fouls" : {"$avg": "$player_stats.fouls"},
            "overall fouls" : {"$sum": "$player_stats.fouls"}
        }
    },
    {
        "$project": {
            "_id": 0, "team": "$_id", "average fouls": 1, "overall fouls": 1
        }
    }
    
])
pprint(list(fouls))

wins = basketball.aggregate([
    {
        "$match": {
            "$and": [{"team_id" : "ADMU"}, {"result" : "WIN"}]
        }
    },
    {
        "$group": {
            "_id": "$player_id", # group by player id to conveniently limit later and avoid situations where different players from same game add to sum
            "team" : {"$first": "$team_id"},
            "total wins" : {"$sum": 1}
        }
    },
    {
      "$project" : {
          "_id": 0,
          "team": 1,
          "total wins": 1
      }
    },
    {
        "$limit": 1
    }
])
pprint(list(wins))

# we now look at individual games, let's first see the games with the top 10 highest overall scores to choose a game of interest, and project the teams who got these scores
highscores = basketball.aggregate([
    {
        "$group": {
            "_id" : "$game_id",
            "winner score" : {"$max": "$score"}
        }
    },
    {
        "$sort": {"winner score": -1}
    },
    {
        "$limit": 10
    }
])
pprint(list(highscores))

performance = basketball.aggregate([
    {
        "$match": {"game_id": "2018-8"} # highest scored game
    },
    {
        "$group": {
            "_id": {"$concat": ["$first_name"," ","$last_name"]},
            "team": {"$first": "$team_id"},
            "team result": {"$first": "$result"},
            "reb" : {"$first": "$player_stats.reb"},
            "ast" : {"$first": "$player_stats.ast"},
            "stl" : {"$first": "$player_stats.stl"},
            "blk" : {"$first": "$player_stats.blk"},
            "2ptpct" : {"$first": "$player_stats.2pt_pct"},
            "3ptpct" : {"$first": "$player_stats.3pt_pct"}
        }
    },
    {
        "$project": {
            "_id" : 0,
            "team": 1,
            "team result": 1,
            "MVP": "$_id",
            "rating": {"$avg" : ["$reb","$ast","$stl","$blk","$2ptpct","3ptpct"]}
        }
    },
    {
        "$sort": {"rating": -1}
    },
    {
        "$limit": 1
    }
])
pprint(list(performance))

# We can also perform more complicated queries to determine overall performance in a season
# A statistical point (SP) is used in the league as the primary indicator on who shall win the seasonal MVP award.
# It is based off the cumulative statistics a player has garnered throughout the season.
# SP = 1*pts + 1*reb + 1*ast + 1*stl + 1*blk - 1*TO - 0.8*fouls

season_mvp = basketball.aggregate([
    {
        "$match" : {
            "season" : 2016
        }
    },
    {
        "$group" : {
            "_id" : {
                "player" : {"$concat" : ["$first_name", " ", "$last_name"]},
                "team" : "$team_id"
            },
            "pts" : {"$avg" : "$player_stats.pts"},
            "reb" : {"$avg" : "$player_stats.reb"},
            "ast" : {"$avg" : "$player_stats.ast"},
            "stl" : {"$avg" : "$player_stats.stl"},
            "blk" : {"$avg" : "$player_stats.blk"},
            "TO" : {"$avg" : "$player_stats.TO"},
            "fouls" : {"$avg" : "$player_stats.fouls"}
        }
    },
    {
        "$project" : {
            "_id" : 0,
            "team": "$_id.team",
            "player" : "$_id.player",
            "SP" : {
                "$sum" : [
                    {"$multiply" : ["$pts", 1]},
                    {"$multiply" : ["$reb", 1]},
                    {"$multiply" : ["$ast", 1]},
                    {"$multiply" : ["$stl", 1]},
                    {"$multiply" : ["$blk", 1]},
                    {"$multiply" : ["$TO", -1]},
                    {"$multiply" : ["$fouls", -0.8]}
                ]
            }
        }
    },
    {
        "$sort" : {"SP" : -1}
    },
    {
        "$limit" : 1
    }
])


pprint(list(season_mvp))

# Meanwhile, the First and Second Team lineup is comprised of the top 1-5, 6-10 SP leaders.
# Season 2016 First Team
season_firstteam = basketball.aggregate([
    {
        "$match" : {
            "season" : 2016
        }
    },
    {
        "$group" : {
            "_id" : {
                "player" : {"$concat" : ["$first_name", " ", "$last_name"]},
                "team" : "$team_id"
            },
            "pts" : {"$avg" : "$player_stats.pts"},
            "reb" : {"$avg" : "$player_stats.reb"},
            "ast" : {"$avg" : "$player_stats.ast"},
            "stl" : {"$avg" : "$player_stats.stl"},
            "blk" : {"$avg" : "$player_stats.blk"},
            "TO" : {"$avg" : "$player_stats.TO"},
            "fouls" : {"$avg" : "$player_stats.fouls"}
        }
    },
    {
        "$project" : {
            "_id" : 0,
            "team": "$_id.team",
            "player" : "$_id.player",
            "SP" : {
                "$sum" : [
                    {"$multiply" : ["$pts", 1]},
                    {"$multiply" : ["$reb", 1]},
                    {"$multiply" : ["$ast", 1]},
                    {"$multiply" : ["$stl", 1]},
                    {"$multiply" : ["$blk", 1]},
                    {"$multiply" : ["$TO", -1]},
                    {"$multiply" : ["$fouls", -0.8]}
                ]
            }
        }
    },
    {
        "$sort" : {"SP" : -1}
    },
    {
        "$limit" : 5
    }
])

pprint(list(season_firstteam))

# Season 2019 Second Team
season_secondteam = basketball.aggregate([
    {
        "$match" : {
            "season" : 2016
        }
    },
    {
        "$group" : {
            "_id" : {
                "player" : {"$concat" : ["$first_name", " ", "$last_name"]},
                "team" : "$team_id"
            },
            "pts" : {"$avg" : "$player_stats.pts"},
            "reb" : {"$avg" : "$player_stats.reb"},
            "ast" : {"$avg" : "$player_stats.ast"},
            "stl" : {"$avg" : "$player_stats.stl"},
            "blk" : {"$avg" : "$player_stats.blk"},
            "TO" : {"$avg" : "$player_stats.TO"},
            "fouls" : {"$avg" : "$player_stats.fouls"}
        }
    },
    {
        "$project" : {
            "_id" : 0,
            "team": "$_id.team",
            "player" : "$_id.player",
            "SP" : {
                "$sum" : [
                    {"$multiply" : ["$pts", 1]},
                    {"$multiply" : ["$reb", 1]},
                    {"$multiply" : ["$ast", 1]},
                    {"$multiply" : ["$stl", 1]},
                    {"$multiply" : ["$blk", 1]},
                    {"$multiply" : ["$TO", -1]},
                    {"$multiply" : ["$fouls", -0.8]}
                ]
            }
        }
    },
    {
        "$sort" : {"SP" : -1}
    },
    {
        "$skip" : 5
    },
    {
        "$limit" : 5
    }
])

pprint(list(season_secondteam))