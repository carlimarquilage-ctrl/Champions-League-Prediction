import pandas as pd

# Tells pandas not to hide columns because the terminal is narrow.
pd.set_option("display.max_columns", None)

matches = pd.read_csv("data/Full_Dataset.csv")

champions_league = matches[matches["Competition"] == "uefa-champions-league"]

champions_league = champions_league[champions_league["Location"] == "Home"]

clean_matches = champions_league[
    [
        "Date",
        "season",
        "Team",
        "Opponent",
        "Team_Score",
        "Opponent_Score"
    ]
].copy()

clean_matches = clean_matches.rename(
    columns={
        "Date": "date",
        "season": "season",
        "Team": "home_team",
        "Opponent": "away_team",
        "Team_Score": "home_goals",
        "Opponent_Score": "away_goals"
    }
)

missing_scores = clean_matches[
    clean_matches["home_goals"].isnull()
]

clean_matches = clean_matches.dropna(
    subset=["home_goals", "away_goals"]
)

clean_matches["home_goals"] = clean_matches["home_goals"].astype(int)
clean_matches["away_goals"] = clean_matches["away_goals"].astype(int)

clean_matches["date"] = pd.to_datetime(
    clean_matches["date"],
    format="%d/%m/%Y"
)

clean_matches["date"] = clean_matches["date"].dt.strftime('%Y-%m-%d')

# print(clean_matches.head())
# print(champions_league.shape) - looks at one value of each row
