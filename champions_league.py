import pandas as pd
import numpy as np
import sqlite3
from main import clean_matches
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report


# Goals:

# Load and clean Champions League match data

# Store cleaned matches in SQLite

# Generate historical features using only matches before the current match

# SQL and Data Base

# If the file does not exist, creates a new one
connection = sqlite3.connect("champions_league.db")
# the cursor- pipeline to the data base file you create and then you can manipulate it.
cursor = connection.cursor()

cursor.execute("""
DELETE FROM matches;
""")

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

connection.commit()

features = []


def get_historical_data(cursor, match_date, home_team, away_team):
    # Historical home performance
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

    # Historical away performance
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

    return home_stats, away_stats


def get_recent_matches(cursor, team, match_date):  # Retrieve a teams last 5 matches
    # Recent match home history
    cursor.execute("""
    SELECT home_team, away_team, home_goals, away_goals
    FROM matches
    WHERE date < ?
    AND (home_team = ? OR away_team = ?)
    ORDER BY date DESC
    LIMIT 5
    """, (match_date, team, team))

    return cursor.fetchall()


def calculate_recent_form(recent_matches, team):
    total_goals_scored = 0
    total_goals_conceded = 0
    recent_wins = 0

    for recent_match in recent_matches:
        if recent_match[0] == team:
            goals_scored = recent_match[2]
            goals_conceded = recent_match[3]
        elif recent_match[1] == team:
            goals_scored = recent_match[3]
            goals_conceded = recent_match[2]
        total_goals_conceded += goals_conceded
        total_goals_scored += goals_scored

        if goals_scored > goals_conceded:
            recent_wins += 1

    if len(recent_matches) > 0:
        recent_avg_goals = (total_goals_scored)/(len(recent_matches))
        recent_avg_conceded = (total_goals_conceded)/(len(recent_matches))
        recent_win_rate = (recent_wins / len(recent_matches))*100
    else:
        recent_avg_goals = 0
        recent_avg_conceded = 0
        recent_win_rate = 0

    return recent_avg_conceded, recent_avg_goals, recent_win_rate


def main():
    for match in clean_matches.itertuples(index=False):
        match_date = match.date
        home_team = match.home_team
        away_team = match.away_team

        home_stats, away_stats = get_historical_data(
            cursor, match_date, home_team, away_team
        )

        # Skips matches where either team has no prior home/away history
        if home_stats == None or away_stats == None:
            continue

        home_recent_matches = get_recent_matches(cursor, home_team, match_date)
        away_recent_matches = get_recent_matches(cursor, away_team, match_date)

        # Tuple unpacking
        home_recent_avg_conceded, home_recent_avg_goals, home_recent_win_rate = calculate_recent_form(
            home_recent_matches,  home_team)
        away_recent_avg_conceded, away_recent_avg_goals, away_recent_win_rate = calculate_recent_form(
            away_recent_matches, away_team)

        if match.home_goals > match.away_goals:  # Creating variable for match outcome
            result = "H"
        elif match.home_goals == match.away_goals:
            result = "D"
        else:
            result = "A"

        # Making the features to input into the machine learning pipeline
        home_matches = home_stats[1]
        home_avg_goals = home_stats[2]
        home_conceded_goals = home_stats[3]
        home_win_rate = home_stats[7]

        away_matches = away_stats[1]
        away_avg_goals = away_stats[2]
        away_conceded_goals = away_stats[3]
        away_win_rate = away_stats[7]

        features.append({
            "date": match_date,

            # Historical home performance
            "home_matches": home_matches,
            "home_avg_goals": home_avg_goals,
            "home_avg_conceded": home_conceded_goals,
            "home_win_rate": home_win_rate,

            # Historical away performance
            "away_matches": away_matches,
            "away_avg_goals": away_avg_goals,
            "away_avg_conceded": away_conceded_goals,
            "away_win_rate": away_win_rate,

            # Recent home-team form
            "home_recent_avg_goals": home_recent_avg_goals,
            "home_recent_avg_conceded": home_recent_avg_conceded,
            "home_recent_win_rate": home_recent_win_rate,

            # Recent away-team form
            "away_recent_avg_goals": away_recent_avg_goals,
            "away_recent_avg_conceded": away_recent_avg_conceded,
            "away_recent_win_rate": away_recent_win_rate,

            "win_rate_difference": home_win_rate - away_win_rate,
            "attack_difference": home_avg_goals - away_avg_goals,
            "recent_form_difference": home_recent_win_rate - away_recent_win_rate,

            # Target
            "result": result,
        })      # Adding each feature needed for the machine learning model to the features array

        # Converting engineered features into a DataFrame for model training
        # Turning the features array into a dataframe for easier accessiblity
    training_data = pd.DataFrame(features)
    training_data = training_data.sort_values(
        "date").reset_index(drop=True)  # Sort the data by date

    train_model(training_data)


def train_model(training_data):
    y = training_data["result"]
    x = training_data.drop(columns=["date", "result"])

    # Creating the index for the split
    split_index = int(len(training_data)*0.8)

    # Seperating the test data into 80% training 20% testing
    x_train = x.iloc[:split_index]
    x_test = x.iloc[split_index:]

    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    scaler = StandardScaler()

    # Learn the mean and standard deviation value and use learned values to scale x_train
    x_train_scaled = scaler.fit_transform(x_train)
    # Use the learned features in the future
    x_test_scaled = scaler.transform(x_test)

    # Tells the model to take notice of models that are not as frequent
    model = LogisticRegression(class_weight="balanced", max_iter=100)
    model.fit(x_train_scaled, y_train)  # Method to train the model

    predictions = model.predict(x_test_scaled)

    accuracy = accuracy_score(y_test, predictions)

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=["H", "D", "A"]
    )

    print(f"Accuracy: {accuracy:.2%}")

    print("\nConfusion Matrix (H, D, A):")
    print(matrix)

    print("\nClassification Report")
    print(classification_report(y_test, predictions))

    """print("X type:", type(x))
    print("X shape:", x.shape)
    print("Y type:", type(y))
    print("Y shape:", y.shape)"""


if __name__ == "__main__":
    main()
