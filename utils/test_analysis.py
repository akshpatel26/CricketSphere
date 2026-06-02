"""
test_analysis.py
All analysis helpers for the Test Rankings page.
Column names match exactly what's in the CSVs.
"""

import pandas as pd
import numpy as np


def _safe_div(num: pd.Series, den: pd.Series, scale: float = 1.0) -> pd.Series:
    return (num / den.replace(0, np.nan) * scale).fillna(0).round(2)


# ── Tab 1: Countries & Venues ─────────────────────────────────────────────────

def get_matches_by_country(matches_df: pd.DataFrame) -> pd.DataFrame:
    if matches_df is None or matches_df.empty:
        return pd.DataFrame(columns=["Country", "Matches"])

    if "Match Venue (Country)" in matches_df.columns:
        df = matches_df["Match Venue (Country)"].value_counts().reset_index()
        df.columns = ["Country", "Matches"]
        return df

    return pd.DataFrame(columns=["Country", "Matches"])

def get_matches_by_venue(matches_df: pd.DataFrame) -> pd.DataFrame:
    if matches_df is None or matches_df.empty:
        return pd.DataFrame(columns=["Venue", "Matches"])

    if "Match Venue (Stadium)" in matches_df.columns:
        df = matches_df["Match Venue (Stadium)"].value_counts().reset_index()
        df.columns = ["Venue", "Matches"]
        return df

    return pd.DataFrame(columns=["Venue", "Matches"])



# ── Tab 2: Top Wicket Takers ──────────────────────────────────────────────────

def get_top_wicket_takers(
    bowling_df: pd.DataFrame,
    players_df: pd.DataFrame = None,
    team: str = "All",
    innings: str = "All",
    min_wickets: int = 5,
) -> pd.DataFrame:
    """
    bowling_df columns: Match ID, innings, team, opposition, bowler id,
                        overs, balls, maidens, conceded, wickets,
                        economy, dots, fours, sixes, wides, noballs
    """
    if bowling_df is None or bowling_df.empty:
        return pd.DataFrame()

    df = bowling_df.copy()

    if team != "All" and "team" in df.columns:
        df = df[df["team"] == team]
    if innings != "All" and "innings" in df.columns:
        df = df[df["innings"] == int(innings)]

    agg = (
        df.groupby("bowler id")
        .agg(
            Matches   = ("Match ID", "nunique"),
            Wickets   = ("wickets",  "sum"),
            Balls     = ("balls",    "sum"),
            Runs      = ("conceded", "sum"),
            Maidens   = ("maidens",  "sum"),
        )
        .reset_index()
        .rename(columns={"bowler id": "Player ID"})
    )

    agg["Overs"]       = (agg["Balls"] // 6).astype(str) + "." + (agg["Balls"] % 6).astype(str)
    agg["Average"]     = _safe_div(agg["Runs"],  agg["Wickets"])
    agg["Strike Rate"] = _safe_div(agg["Balls"], agg["Wickets"])
    agg["Economy"]     = _safe_div(agg["Runs"],  agg["Balls"] / 6)

    # Best bowling in a single innings
    inn_agg = (
        df.groupby(["bowler id", "Match ID", "innings"])
        .agg(inn_wkts=("wickets", "sum"), inn_runs=("conceded", "sum"))
        .reset_index()
        .sort_values("inn_wkts", ascending=False)
        .drop_duplicates("bowler id")
        .rename(columns={"bowler id": "Player ID"})
    )
    inn_agg["Best"] = (
        inn_agg["inn_wkts"].astype(int).astype(str)
        + "/"
        + inn_agg["inn_runs"].astype(int).astype(str)
    )
    agg = agg.merge(inn_agg[["Player ID", "Best"]], on="Player ID", how="left")

    agg = agg[agg["Wickets"] >= min_wickets].sort_values("Wickets", ascending=False)

    if players_df is not None and not players_df.empty:
        agg = agg.merge(
            players_df[["player_id", "player_name"]],
            left_on="Player ID", right_on="player_id", how="left"
        ).drop(columns=["player_id"])
        first_col = "player_name"
    else:
        first_col = "Player ID"

    ordered = [first_col, "Matches", "Wickets", "Overs", "Balls",
               "Runs", "Maidens", "Average", "Strike Rate", "Economy", "Best"]
    return agg[[c for c in ordered if c in agg.columns]].reset_index(drop=True)


# ── Tab 3: Top Run Scorers ────────────────────────────────────────────────────

def get_top_run_scorers(
    batting_df: pd.DataFrame,
    players_df: pd.DataFrame = None,
    team: str = "All",
    innings: str = "All",
    min_runs: int = 100,
) -> pd.DataFrame:
    """
    batting_df columns: Match ID, innings, team, batsman, runs, balls,
                        fours, sixes, strikeRate, isOut, wicketType,
                        fielders, bowler
    """
    if batting_df is None or batting_df.empty:
        return pd.DataFrame()

    df = batting_df.copy()

    if team != "All" and "team" in df.columns:
        df = df[df["team"] == team]
    if innings != "All" and "innings" in df.columns:
        df = df[df["innings"] == int(innings)]

    # Runs per innings (for HS, 50s, 100s)
    inn_runs = (
        df.groupby(["batsman", "Match ID", "innings"])["runs"]
        .sum().reset_index()
    )

    hs = inn_runs.groupby("batsman")["runs"].max().reset_index().rename(columns={"runs": "HS"})
    fifties  = inn_runs[inn_runs["runs"].between(50, 99)].groupby("batsman").size().reset_index(name="50s")
    hundreds = inn_runs[inn_runs["runs"] >= 100].groupby("batsman").size().reset_index(name="100s")

    agg = (
        df.groupby("batsman")
        .agg(
            Matches    = ("Match ID", "nunique"),
            Innings    = ("innings",  "count"),
            Runs       = ("runs",     "sum"),
            Balls      = ("balls",    "sum"),
            Fours      = ("fours",    "sum"),
            Sixes      = ("sixes",    "sum"),
            Dismissals = ("isOut",    "sum"),
        )
        .reset_index()
        .rename(columns={"batsman": "Player ID"})
    )

    agg["Dismissals"] = agg["Dismissals"].astype(int)
    agg["Average"]    = _safe_div(agg["Runs"], agg["Dismissals"])
    agg["Strike Rate"]= _safe_div(agg["Runs"], agg["Balls"], scale=100)

    for extra in [
        hs.rename(columns={"batsman": "Player ID"}),
        fifties.rename(columns={"batsman": "Player ID"}),
        hundreds.rename(columns={"batsman": "Player ID"}),
    ]:
        agg = agg.merge(extra, on="Player ID", how="left")

    for col in ["HS", "50s", "100s"]:
        if col in agg.columns:
            agg[col] = agg[col].fillna(0).astype(int)

    agg = agg[agg["Runs"] >= min_runs].sort_values("Runs", ascending=False)

    if players_df is not None and not players_df.empty:
        agg = agg.merge(
            players_df[["player_id", "player_name"]],
            left_on="Player ID", right_on="player_id", how="left"
        ).drop(columns=["player_id"])
        first_col = "player_name"
    else:
        first_col = "Player ID"

    ordered = [first_col, "Matches", "Innings", "Runs", "Balls",
               "HS", "Average", "Strike Rate", "100s", "50s",
               "Fours", "Sixes", "Dismissals"]
    return agg[[c for c in ordered if c in agg.columns]].reset_index(drop=True)


# ── Tab 4: Team Rankings ──────────────────────────────────────────────────────

def get_team_rankings(
    matches_df: pd.DataFrame,
    sort_by: str = "Win %",
) -> pd.DataFrame:
    """
    matches_df columns include: Team1Name, Team2Name, Match Result / WinningTeam
    Tries several common result-column names automatically.
    """
    if matches_df is None or matches_df.empty:
        return pd.DataFrame()

    team1_col = "Team1 Name"   # ← fix
    team2_col = "Team2 Name"   # ← fix
    winner_col = "Match Winner"  # ← fix

    if team1_col not in matches_df.columns or team2_col not in matches_df.columns:
        return pd.DataFrame()

    # Auto-detect winner column
    winner_col = None
    for c in ["WinningTeam", "Winner", "winner", "Match Winner",
              "Match Result", "result", "Result"]:
        if c in matches_df.columns:
            winner_col = c
            break

    all_teams = sorted(
        pd.concat([matches_df[team1_col], matches_df[team2_col]]).dropna().unique()
    )

    records = []
    for team in all_teams:
        tm = matches_df[
            (matches_df[team1_col] == team) | (matches_df[team2_col] == team)
        ]
        total = len(tm)
        wins = losses = draws = 0

        if winner_col:
            col_vals = tm[winner_col].astype(str).str.strip().str.lower()
            team_lower = team.lower()
            for _, row in tm.iterrows():
                val = str(row[winner_col]).strip().lower()
                if "draw" in val or "tie" in val or val in ("nan", "", "none"):
                    draws += 1
                elif team_lower in val:
                    wins += 1
                else:
                    losses += 1

        win_pct = round(wins / total * 100, 1) if total > 0 else 0.0
        records.append({
            "Team":    team,
            "Matches": total,
            "Wins":    wins,
            "Losses":  losses,
            "Draws":   draws,
            "Win %":   win_pct,
        })

    df = pd.DataFrame(records)
    sort_col = {"Win %": "Win %", "Wins": "Wins", "Matches": "Matches"}.get(sort_by, "Win %")
    return df.sort_values([sort_col, "Wins"], ascending=False).reset_index(drop=True)


# ── Tab 5: Dot Ball Analysis ──────────────────────────────────────────────────

def get_dot_ball_by_bowler(
    bowling_df: pd.DataFrame,
    players_df: pd.DataFrame = None,
    team: str = "All",
    min_balls: int = 60,
) -> pd.DataFrame:
    if bowling_df is None or bowling_df.empty:
        return pd.DataFrame()

    df = bowling_df.copy()
    if team != "All" and "team" in df.columns:
        df = df[df["team"] == team]

    agg = (
        df.groupby("bowler id")
        .agg(
            Matches = ("Match ID", "nunique"),
            Balls   = ("balls",    "sum"),
            Dots    = ("dots",     "sum"),
            Wickets = ("wickets",  "sum"),
            Runs    = ("conceded", "sum"),
        )
        .reset_index()
        .rename(columns={"bowler id": "Player ID"})
    )

    agg = agg[agg["Balls"] >= min_balls]
    agg["Dot Ball %"] = _safe_div(agg["Dots"], agg["Balls"], scale=100)
    agg["Economy"]    = _safe_div(agg["Runs"], agg["Balls"] / 6)
    agg = agg.sort_values("Dot Ball %", ascending=False)

    if players_df is not None and not players_df.empty:
        agg = agg.merge(
            players_df[["player_id", "player_name"]],
            left_on="Player ID", right_on="player_id", how="left"
        ).drop(columns=["player_id"])
        first_col = "player_name"
    else:
        first_col = "Player ID"

    ordered = [first_col, "Matches", "Balls", "Dots",
               "Dot Ball %", "Wickets", "Runs", "Economy"]
    return agg[[c for c in ordered if c in agg.columns]].reset_index(drop=True)


def get_dot_ball_by_team(
    bowling_df: pd.DataFrame,
    min_balls: int = 60,
) -> pd.DataFrame:
    if bowling_df is None or bowling_df.empty:
        return pd.DataFrame()

    agg = (
        bowling_df.groupby("team")
        .agg(
            Matches = ("Match ID", "nunique"),
            Balls   = ("balls",    "sum"),
            Dots    = ("dots",     "sum"),
            Wickets = ("wickets",  "sum"),
            Runs    = ("conceded", "sum"),
        )
        .reset_index()
        .rename(columns={"team": "Team"})
    )
    agg = agg[agg["Balls"] >= min_balls]
    agg["Dot Ball %"] = _safe_div(agg["Dots"], agg["Balls"], scale=100)
    agg["Economy"]    = _safe_div(agg["Runs"], agg["Balls"] / 6)
    return agg.sort_values("Dot Ball %", ascending=False).reset_index(drop=True)


# ── Bonus: Partnerships ───────────────────────────────────────────────────────

def get_top_partnerships(
    partnership_df: pd.DataFrame,
    players_df: pd.DataFrame = None,
    team: str = "All",
    min_runs: int = 50,
) -> pd.DataFrame:
    """
    partnership_df columns: Match ID, innings, for wicket, team, opposition,
                            player1, player2, player1 runs, player2 runs,
                            player1 balls, player2 balls,
                            partnership runs, partnership balls
    """
    if partnership_df is None or partnership_df.empty:
        return pd.DataFrame()

    df = partnership_df.copy()
    if team != "All" and "team" in df.columns:
        df = df[df["team"] == team]

    df = df[df["partnership runs"] >= min_runs].sort_values(
        "partnership runs", ascending=False
    )

    # Merge player names for player1 and player2
    if players_df is not None and not players_df.empty:
        df = df.merge(
            players_df[["player_id", "player_name"]].rename(
                columns={"player_id": "player1", "player_name": "Player 1"}
            ),
            on="player1", how="left"
        )
        df = df.merge(
            players_df[["player_id", "player_name"]].rename(
                columns={"player_id": "player2", "player_name": "Player 2"}
            ),
            on="player2", how="left"
        )

    return df.reset_index(drop=True)


# ── Bonus: Fall of Wickets ────────────────────────────────────────────────────

def get_fow_summary(
    fow_df: pd.DataFrame,
    team: str = "All",
) -> pd.DataFrame:
    """
    fow_df columns: Match ID, innings, team, player, wicket, over, runs
    """
    if fow_df is None or fow_df.empty:
        return pd.DataFrame()

    df = fow_df.copy()
    if team != "All" and "team" in df.columns:
        df = df[df["team"] == team]
    return df.reset_index(drop=True)