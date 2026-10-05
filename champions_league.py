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

features = []

for match in clean_matches.itertuples(index=False):  # Iterates over tuple
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

    if match.home_goals > match.away_goals:  # Creating variable for match outcome
        result = "H"
    elif match.home_goals == match.away_goals:
        result = "D"
    else:
        result = "A"

    # Skips matches where either team has no prior home/away history
    if home_stats == None or away_stats == None:
        continue

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
        "home_matches": home_matches,
        "home_avg_goals": home_avg_goals,
        "home_avg_conceded": home_conceded_goals,
        "home_win_rate":    home_win_rate,

        "away_matches": away_matches,
        "away_avg_goals": away_avg_goals,
        "away_avg_conceded": away_conceded_goals,
        "away_win_rate": away_win_rate,

        "result": result,
    })  # Adding each feature needed for the machine learning model to the features array

# Converting engineered features into a DataFrame for model training
training_data = pd.DataFrame(features)

y = training_data["result"]  # Create y
x = training_data.drop(columns=["date", "result"])  # Prevents target leakage -


split_index = int(len(training_data)*0.8)  # Creating the index for the split

# Seperating the test data into 80% training 20% testing
x_train = x.iloc[:split_index]
x_test = x.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]

print(x_train.shape)
print(x_test.shape)
print(y_train.shape)
print(y_test.shape)

scaler = StandardScaler()
# Learn the mean and standard deviation value and use learned values to scale x_train
x_train_scaled = scaler.fit_transform(x_train)
# Use the learned features in the future
x_test_scaled = scaler.transform(x_test)

model = LogisticRegression()
# Makes the max iteration be 100, if it goes over, the model will not be as optimized

# Tells the model to take notice of models that are not as frequent
model = LogisticRegression(class_weight="balanced")

LogisticRegression(max_iter=100)
model.fit(x_train_scaled, y_train)  # Method to train the model

predictions = model.predict(x_test_scaled)

accuracy = accuracy_score(y_test, predictions)

matrix = confusion_matrix(
    y_test,
    predictions,
    labels=["H", "D", "A"]
)
print(matrix)
print(classification_report(y_test, predictions))
