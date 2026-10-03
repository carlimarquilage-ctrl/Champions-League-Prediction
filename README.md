# Champions League Match Predictor ⚽

A machine learning project for predicting UEFA Champions League match outcomes using historical match data.

The project is being built as an end-to-end data and machine learning pipeline using Python, Pandas, SQL, and eventually scikit-learn and FastAPI.

## Current Pipeline

Raw Champions League match data  
↓  
Pandas data cleaning  
↓  
SQLite database  
↓  
SQL historical statistics  
↓  
Feature engineering  
↓  
Machine learning model *(in progress)*  
↓  
FastAPI prediction API *(planned)*

## Features

For each historical match, statistics are calculated using only matches that occurred **before that match** to prevent data leakage.

Current features include:

- Home matches played
- Home average goals scored
- Home average goals conceded
- Home win rate
- Away matches played
- Away average goals scored
- Away average goals conceded
- Away win rate

The target variable is the match result:

- `H` — Home win
- `D` — Draw
- `A` — Away win

## Dataset

The project uses historical European soccer data from the Kaggle **European Soccer Data** dataset.

The raw dataset is not included in this repository.

After cleaning the Champions League data, the project contains 2,526 matches with valid scores. Historical feature generation currently produces 2,326 usable training examples after removing matches where one of the teams has no required prior history.

## Technologies

- Python
- Pandas
- SQLite
- SQL
- scikit-learn *(next stage)*
- FastAPI *(planned)*

## Project Status

🚧 Work in progress.

Current progress:

- [x] Clean raw match data
- [x] Filter UEFA Champions League matches
- [x] Build SQLite match database
- [x] Calculate historical team statistics with SQL
- [x] Prevent future-data leakage using match dates
- [x] Generate match-level feature dataset
- [x] Convert features into a Pandas DataFrame
- [ ] Prepare training and testing datasets
- [ ] Train baseline classification model
- [ ] Evaluate model performance
- [ ] Generate match probabilities
- [ ] Build prediction API with FastAPI

## Goal

The goal is to build a model that takes information known before a Champions League match and predicts the probabilities of a home win, draw, or away win.
