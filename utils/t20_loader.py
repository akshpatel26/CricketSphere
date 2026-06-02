"""
t20_loader.py  –  T20 International Data Loader & Cleaner
Loads and standardizes the 5 T20I CSV files:
  - t20i_Matches_Data.csv
  - t20i_Batting_Card.csv
  - t20i_Bowling_Card.csv
  - t20i_Fow_Card.csv          (Fall of Wickets)
  - t20i_Partnership_Card.csv
  - players_info.csv
"""

import os
import pandas as pd
import numpy as np
from functools import lru_cache

# ── Path helpers ───────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def _path(filename: str) -> str:
    return os.path.join(DATA_DIR, filename)


# ── Country / team name normalisation map ─────────────────────────────────────
COUNTRY_MAP = {
    "U.S.A.": "USA",
    "United States of America": "USA",
    "United Arab Emirates": "UAE",
    "P.N.G.": "Papua New Guinea",
    "W.Indies": "West Indies",
    "West Indies": "West Indies",
    "Windies": "West Indies",
    "ICC World XI": "World XI",
    "Asia XI": "Asia XI",
    "Africa XI": "Africa XI",
}


def _normalise_country(series: pd.Series) -> pd.Series:
    return series.replace(COUNTRY_MAP).str.strip()


# ── Date parser ────────────────────────────────────────────────────────────────
def _parse_date(series: pd.Series) -> pd.Series:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%b %d, %Y", "%d %b %Y"):
        try:
            return pd.to_datetime(series, format=fmt, errors="coerce")
        except Exception:
            pass
    return pd.to_datetime(series, infer_datetime_format=True, errors="coerce")


# ══════════════════════════════════════════════════════════════════════════════
# Individual loaders
# ══════════════════════════════════════════════════════════════════════════════

@lru_cache(maxsize=1)
def load_t20_matches() -> pd.DataFrame:
    """Load t20i_Matches_Data.csv and return a clean DataFrame."""
    path = _path("t20i_Matches_Data.csv")
    df = pd.read_csv(path, low_memory=False)

    # ── Rename columns to a consistent schema ─────────────────────────────────
    col_rename = {
        "Match ID":         "match_id",
        "T20I Match No":    "t20i_match_no",
        "Match No":         "match_no",
        "Series ID":        "series_id",
        "Series Name":      "series_name",
        "Match Date":       "date",
        "Match Format":     "format",
        "Ground ID":        "ground_id",
        "Team1 ID":         "team1_id",
        "Team1 City":       "team1_city",
        "Team1 Country":    "team1",
        "Team1 Runs":       "team1_runs",
        "Team1 Wickets":    "team1_wickets",
        "Team1 Extras":     "team1_extras",
        "Team1 Balls":      "team1_balls",
        "Team2 ID":         "team2_id",
        "Team2 City":       "team2_city",
        "Team2 Country":    "team2",
        "Team2 Runs":       "team2_runs",
        "Team2 Wickets":    "team2_wickets",
        "Team2 Extras":     "team2_extras",
        "Team2 Balls":      "team2_balls",
        "Match Venue":      "venue",
        "Match Result":     "result",
        "Match Winning Team": "winner",
        "Toss Winner":      "toss_winner",
        "Toss Verdict":     "toss_decision",
        "Umpire 1":         "umpire1",
        "Umpire 2":         "umpire2",
        "MOM Player":   "man_of_match",
        "MOM Player 1": "man_of_match",
        "Team1 Players":    "team1_players",
        "Team2 Players":    "team2_players",
        "Debut Players":    "debut_players",
    }
    # Only rename columns that actually exist
    df = df.rename(columns={k: v for k, v in col_rename.items() if k in df.columns})

    # ── Lower-case flexible fallback for any remaining mixed-case cols ─────────
    df.columns = [c.strip() for c in df.columns]

    # ── Date ──────────────────────────────────────────────────────────────────
    if "date" in df.columns:
        df["date"] = _parse_date(df["date"])
        df["year"]  = df["date"].dt.year
        df["month"] = df["date"].dt.month

    # ── Country normalise ─────────────────────────────────────────────────────
    for col in ("team1", "team2", "winner", "toss_winner"):
        if col in df.columns:
            df[col] = _normalise_country(df[col].astype(str))

    # ── Numeric coerce ────────────────────────────────────────────────────────
    for col in ("team1_runs", "team2_runs", "team1_wickets", "team2_wickets",
                "team1_balls", "team2_balls", "team1_extras", "team2_extras"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ── host_country: derive from venue string if not present ─────────────────
    if "host_country" not in df.columns and "venue" in df.columns:
        # Last comma-separated word of venue is usually the country
        df["host_country"] = (
            df["venue"].astype(str)
            .str.split(",").str[-1]
            .str.strip()
        )
        df["host_country"] = _normalise_country(df["host_country"])

    return df.reset_index(drop=True)


@lru_cache(maxsize=1)
def load_t20_batting() -> pd.DataFrame:
    """Load t20i_Batting_Card.csv."""
    df = pd.read_csv(_path("t20i_Batting_Card.csv"), low_memory=False)
    col_rename = {
        "Match ID":    "match_id",
        "innings":     "innings",
        "team":        "team",
        "batsman":     "batsman_id",
        "runs":        "runs",
        "balls":       "balls",
        "fours":       "fours",
        "sixes":       "sixes",
        "strikeRate":  "strike_rate",
        "isOut":       "is_out",
        "wicketType":  "wicket_type",
        "fielders":    "fielders",
        "bowler":      "bowler_id",
    }
    df = df.rename(columns={k: v for k, v in col_rename.items() if k in df.columns})
    df.columns = [c.strip() for c in df.columns]

    for col in ("runs", "balls", "fours", "sixes", "strike_rate"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "team" in df.columns:
        df["team"] = _normalise_country(df["team"].astype(str))

    return df.reset_index(drop=True)


@lru_cache(maxsize=1)
def load_t20_bowling() -> pd.DataFrame:
    """Load t20i_Bowling_Card.csv."""
    df = pd.read_csv(_path("t20i_Bowling_Card.csv"), low_memory=False)
    col_rename = {
        "Match ID":   "match_id",
        "innings":    "innings",
        "team":       "team",
        "opposition": "opposition",
        "bowler id":  "bowler_id",
        "overs":      "overs",
        "balls":      "balls",
        "maidens":    "maidens",
        "conceded":   "runs_conceded",
        "wickets":    "wickets",
        "economy":    "economy",
        "dots":       "dots",
        "fours":      "fours",
        "sixes":      "sixes",
        "wides":      "wides",
        "noballs":    "no_balls",
    }
    df = df.rename(columns={k: v for k, v in col_rename.items() if k in df.columns})
    df.columns = [c.strip() for c in df.columns]

    for col in ("overs", "balls", "maidens", "runs_conceded", "wickets",
                "economy", "dots", "fours", "sixes", "wides", "no_balls"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ("team", "opposition"):
        if col in df.columns:
            df[col] = _normalise_country(df[col].astype(str))

    return df.reset_index(drop=True)


@lru_cache(maxsize=1)
def load_t20_fow() -> pd.DataFrame:
    """Load t20i_Fow_Card.csv (Fall of Wickets)."""
    df = pd.read_csv(_path("t20i_Fow_Card.csv"), low_memory=False)
    col_rename = {
        "Match ID": "match_id",
        "innings":  "innings",
        "team":     "team",
        "player":   "player_id",
        "wicket":   "wicket_no",
        "over":     "over",
        "runs":     "runs_at_fall",
    }
    df = df.rename(columns={k: v for k, v in col_rename.items() if k in df.columns})
    df.columns = [c.strip() for c in df.columns]

    for col in ("wicket_no", "over", "runs_at_fall"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "team" in df.columns:
        df["team"] = _normalise_country(df["team"].astype(str))

    return df.reset_index(drop=True)


@lru_cache(maxsize=1)
def load_t20_partnerships() -> pd.DataFrame:
    """Load t20i_Partnership_Card.csv."""
    df = pd.read_csv(_path("t20i_Partnership_Card.csv"), low_memory=False)
    col_rename = {
        "Match ID":          "match_id",
        "innings":           "innings",
        "for wicket":        "for_wicket",
        "team":              "team",
        "opposition":        "opposition",
        "player1":           "player1_id",
        "player2":           "player2_id",
        "player1 runs":      "player1_runs",
        "player2 runs":      "player2_runs",
        "player1 balls":     "player1_balls",
        "player2 balls":     "player2_balls",
        "partnership":       "partnership_runs",
        "partnership balls": "partnership_balls",
    }
    df = df.rename(columns={k: v for k, v in col_rename.items() if k in df.columns})
    df.columns = [c.strip() for c in df.columns]

    for col in ("for_wicket", "player1_runs", "player2_runs",
                "player1_balls", "player2_balls",
                "partnership_runs", "partnership_balls"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ("team", "opposition"):
        if col in df.columns:
            df[col] = _normalise_country(df[col].astype(str))

    return df.reset_index(drop=True)


@lru_cache(maxsize=1)
def load_players_info() -> pd.DataFrame:
    """Load players_info.csv."""
    df = pd.read_csv(_path("players_info.csv"), low_memory=False)
    col_rename = {
        "player_id":    "player_id",
        "player_obj_id":"player_obj_id",
        "player_name":  "player_name",
        "dob":          "dob",
        "dod":          "dod",
        "gender":       "gender",
        "batting_style":"batting_style",
        "bowling_style":"bowling_style",
        "country_id":   "country_id",
        "image_url":    "image_url",
        "image_metadata":"image_metadata",
    }
    df = df.rename(columns={k: v for k, v in col_rename.items() if k in df.columns})
    df.columns = [c.strip() for c in df.columns]
    return df.reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════════
# Merged / enriched helpers
# ══════════════════════════════════════════════════════════════════════════════

def merge_batting_with_players(batting: pd.DataFrame,
                                players: pd.DataFrame) -> pd.DataFrame:
    """Join batting card with player names."""
    if "player_id" not in players.columns or "batsman_id" not in batting.columns:
        return batting
    merged = batting.merge(
        players[["player_id", "player_name"]],
        left_on="batsman_id", right_on="player_id", how="left"
    ).drop(columns=["player_id"], errors="ignore")
    merged = merged.rename(columns={"player_name": "batsman_name"})
    return merged


def merge_bowling_with_players(bowling: pd.DataFrame,
                                players: pd.DataFrame) -> pd.DataFrame:
    """Join bowling card with player names."""
    if "player_id" not in players.columns or "bowler_id" not in bowling.columns:
        return bowling
    merged = bowling.merge(
        players[["player_id", "player_name"]],
        left_on="bowler_id", right_on="player_id", how="left"
    ).drop(columns=["player_id"], errors="ignore")
    merged = merged.rename(columns={"player_name": "bowler_name"})
    return merged


# ══════════════════════════════════════════════════════════════════════════════
# Analysis helpers (used by t20_analysis.py & the notebook)
# ══════════════════════════════════════════════════════════════════════════════

def matches_hosted_per_country(matches: pd.DataFrame) -> pd.DataFrame:
    """How many T20I matches each country has hosted."""
    col = "host_country" if "host_country" in matches.columns else "venue"
    counts = (
        matches[col]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "country", col: "matches"})
    )
    # Pandas 2.x value_counts returns (value, count) directly
    if counts.columns.tolist() == [col, "count"]:
        counts = counts.rename(columns={col: "country", "count": "matches"})
    return counts


def man_of_match_leaders(matches: pd.DataFrame, players: pd.DataFrame,
                          top_n: int = 10) -> pd.DataFrame:
    """Top Man-of-the-Match award winners."""
    col = "man_of_match" if "man_of_match" in matches.columns else "mom_player_id"
    mom = (
        matches[col].dropna()
        .value_counts()
        .reset_index()
        .rename(columns={"index": "player", col: "awards"})
        .head(top_n)
    )
    if mom.columns.tolist() == [col, "count"]:
        mom = mom.rename(columns={col: "player", "count": "awards"})
    # Attempt to replace IDs with names
    if "mom_player_id" in matches.columns and "player_id" in players.columns:
        id_name = players.set_index("player_id")["player_name"].to_dict()
        mom["player"] = mom["player"].map(id_name).fillna(mom["player"])
    return mom


def highest_wicket_takers(bowling: pd.DataFrame, players: pd.DataFrame,
                           top_n: int = 10) -> pd.DataFrame:
    """Top wicket-takers in T20 Internationals."""
    bow = merge_bowling_with_players(bowling, players)
    name_col = "bowler_name" if "bowler_name" in bow.columns else "bowler_id"
    agg = (
        bow.groupby(name_col)
        .agg(wickets=("wickets", "sum"),
             matches=("match_id", "nunique"),
             runs_conceded=("runs_conceded", "sum"),
             overs=("overs", "sum"))
        .reset_index()
        .rename(columns={name_col: "player"})
    )
    agg["economy"] = (agg["runs_conceded"] / agg["overs"].replace(0, np.nan)).round(2)
    return agg.sort_values("wickets", ascending=False).head(top_n).reset_index(drop=True)


def highest_run_scorers(batting: pd.DataFrame, players: pd.DataFrame,
                         top_n: int = 10) -> pd.DataFrame:
    """Top run-scorers in T20 Internationals."""
    bat = merge_batting_with_players(batting, players)
    name_col = "batsman_name" if "batsman_name" in bat.columns else "batsman_id"
    agg = (
        bat.groupby(name_col)
        .agg(runs=("runs", "sum"),
             balls=("balls", "sum"),
             matches=("match_id", "nunique"),
             sixes=("sixes", "sum"),
             fours=("fours", "sum"))
        .reset_index()
        .rename(columns={name_col: "player"})
    )
    agg["strike_rate"] = (agg["runs"] / agg["balls"].replace(0, np.nan) * 100).round(2)
    return agg.sort_values("runs", ascending=False).head(top_n).reset_index(drop=True)


def most_sixes(batting: pd.DataFrame, players: pd.DataFrame,
               level: str = "player", top_n: int = 10) -> pd.DataFrame:
    """Most sixes – either by player or by team."""
    bat = merge_batting_with_players(batting, players)
    if level == "player":
        name_col = "batsman_name" if "batsman_name" in bat.columns else "batsman_id"
        agg = (
            bat.groupby(name_col)["sixes"]
            .sum()
            .reset_index()
            .rename(columns={name_col: "player"})
            .sort_values("sixes", ascending=False)
            .head(top_n)
        )
    else:  # team
        agg = (
            bat.groupby("team")["sixes"]
            .sum()
            .reset_index()
            .sort_values("sixes", ascending=False)
            .head(top_n)
        )
    return agg.reset_index(drop=True)


def most_successful_teams(matches: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Most wins in T20 Internationals."""
    if "winner" not in matches.columns:
        return pd.DataFrame()
    wins = (
        matches["winner"].dropna()
        .value_counts()
        .reset_index()
        .rename(columns={"index": "team", "winner": "wins"})
        .head(top_n)
    )
    if wins.columns.tolist() == ["winner", "count"]:
        wins = wins.rename(columns={"winner": "team", "count": "wins"})

    # Add total matches played
    t1 = matches["team1"].value_counts() if "team1" in matches.columns else pd.Series(dtype=int)
    t2 = matches["team2"].value_counts() if "team2" in matches.columns else pd.Series(dtype=int)
    total = (t1.add(t2, fill_value=0)).reset_index()
    total.columns = ["team", "played"]
    wins = wins.merge(total, on="team", how="left")
    wins["win_pct"] = (wins["wins"] / wins["played"].replace(0, np.nan) * 100).round(1)
    return wins.reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════════
# Convenience: load everything at once
# ══════════════════════════════════════════════════════════════════════════════

def load_all_t20() -> dict:
    """Return a dict with all T20I dataframes."""
    players = load_players_info()
    matches  = load_t20_matches()
    batting  = load_t20_batting()
    bowling  = load_t20_bowling()
    fow      = load_t20_fow()
    partners = load_t20_partnerships()

    return {
        "matches":      matches,
        "batting":      batting,
        "bowling":      bowling,
        "fow":          fow,
        "partnerships": partners,
        "players":      players,
    }