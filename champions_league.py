import pandas as pd
import numpy as np
import sqlite3
from main import clean_matches

# SQL and Data Base

# If the file does not exist, creates a new one
connection = sqlite3.connect("champions_league.db")
# the cursor- oens a pipeline to the data base file you create and then you can manipulate it.
cursor = connection.cursor()

cursor.execute("""
DELETE FROM matches;
""")

connection.commit()

# Itertuples turns each row into something sql can easily consume
rows = clean_matches.itertuples(index=False, name=None)

cursor.executemany("""
INSERT INTO matches(
    date,
    season,
    home_team,
    away_team,
    home_goals,
    away_goals
    ) VALUES(?, ?, ?, ?, ?, ?)""", rows)

match_date = '2018-10-03'

features = []

for match in clean_matches.itertuples(index=False):
    match_date = match.date
    home_team = match.home_team
    away_team = match.away_team

    cursor.execute("""SELECT home_team, COUNT(*) AS matches_played, AVG(home_goals) AS avg_home_goals, AVG(away_goals) AS avg_home_goals_conceded, SUM(
        CASE
            WHEN home_goals > away_goals THEN 1
            ELSE 0
        END
    ) AS home_win,
    SUM(
        CASE
            WHEN home_goals = away_goals THEN 1
            ELSE 0
        END
    ) AS home_draw,
    SUM(
        CASE
            WHEN home_goals < away_goals THEN 1
            ELSE 0
        END
    ) AS home_loss,
    SUM(
        CASE
            WHEN home_goals > away_goals THEN 1
            ELSE 0
        END
        )*100.0/COUNT(*) AS home_win_rate
    FROM matches
    WHERE date < ?
    AND home_team = ?
    GROUP BY home_team
    ORDER BY home_win_rate desc""", (match_date, home_team))

    home_stats = cursor.fetchone()

    cursor.execute("""
    SELECT away_team, COUNT(*) AS matches_played, AVG(away_goals) AS avg_away_goals, AVG(home_goals) AS avg_away_goals_conceded, SUM(
        CASE
            WHEN home_goals < away_goals THEN 1
            ELSE 0
        END
    ) AS away_win,
    SUM(
        CASE
            WHEN home_goals = away_goals THEN 1
            ELSE 0
        END
    ) AS away_draw,
    SUM(
        CASE
            WHEN home_goals > away_goals THEN 1
            ELSE 0
        END
    ) AS away_loss,
    SUM(
        CASE
            WHEN home_goals < away_goals THEN 1
            ELSE 0
        END
        )*100.0/COUNT(*) AS away_win_rate
    FROM matches
    WHERE date < ?
    AND away_team = ?
    GROUP BY away_team
    ORDER BY away_win_rate desc""", (match_date, away_team))

    away_stats = cursor.fetchone()

    if match.home_goals > match.away_goals:
        result = "H"
    elif match.home_goals == match.away_goals:
        result = "D"
    else:
        result = "A"

    if home_stats == None or away_stats == None:
        continue

    home_matches = home_stats[1]
    home_avg_goals = home_stats[2]
    home_conceded_goals = home_stats[3]
    home_win_rate = home_stats[7]

    away_matches = away_stats[1]
    away_avg_goals = away_stats[2]
    away_conceded_goals = away_stats[3]
    away_win_rate = away_stats[7]

    features.append({
        "home_matches": home_matches,
        "home_avg_goals": home_avg_goals,
        "home_avg_conceded": home_conceded_goals,
        "home_win_rate":    home_win_rate,

        "away_matches": away_matches,
        "away_avg_goals": away_avg_goals,
        "away_avg_conceded": away_conceded_goals,
        "away_win_rate": away_win_rate,

        "result": result,
    })

training_data = pd.DataFrame(features)

print(training_data.head())
print(training_data.shape)


# COUNT(*) returns the amoutn of rows
# GROUP BY put rows with the same category together so I can calculate something for each category
# Put ; at the last one
# HAVING: Acts as an if statement
# AS: creates names for the function
