#odi_loader.py
import pandas as pd
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data')

def load_matches():
    df = pd.read_csv(os.path.join(DATA_PATH, 'odi_Matches_Data.csv'))
    df.columns = df.columns.str.strip()
    return df

def load_batting():
    df = pd.read_csv(os.path.join(DATA_PATH, 'odi_Batting_Card.csv'))
    df.columns = df.columns.str.strip()
    return df

def load_bowling():
    df = pd.read_csv(os.path.join(DATA_PATH, 'odi_Bowling_Card.csv'))
    df.columns = df.columns.str.strip()
    return df

def load_fow():
    df = pd.read_csv(os.path.join(DATA_PATH, 'odi_Fow_Card.csv'))
    df.columns = df.columns.str.strip()
    return df

def load_partnership():
    df = pd.read_csv(os.path.join(DATA_PATH, 'odi_Partnership_Card.csv'))
    df.columns = df.columns.str.strip()
    return df

def load_players():
    # Shared with T20 — same players_info.csv
    df = pd.read_csv(os.path.join(DATA_PATH, 'players_info.csv'))
    df.columns = df.columns.str.strip()
    return df

def load_all():
    return {
        'matches':     load_matches(),
        'batting':     load_batting(),
        'bowling':     load_bowling(),
        'fow':         load_fow(),
        'partnership': load_partnership(),
        'players':     load_players(),
    }
