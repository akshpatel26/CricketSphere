"""
t20_analysis.py  –  T20 International Analytics Module
Implements exactly the 6 analysis topics shown in the notebook Table of Contents:
  1. Which country has hosted the most T20I matches?
  2. Top 10 players with most Man-of-the-Match awards
  3. Highest wicket-takers in T20 Internationals
  4. Highest run-scorers in T20 Internationals
  5. Who hit the most sixes?
  6. Most successful teams in T20Is

Each function returns a (DataFrame, plotly.Figure) tuple ready for
display in both the Streamlit app and the Jupyter notebook.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ── shared dark layout ─────────────────────────────────────────────────────────
DARK = dict(
    plot_bgcolor  = "#161b22",
    paper_bgcolor = "#0d1117",
    font_color    = "#e6edf3",
    xaxis = dict(gridcolor="#21262d", linecolor="#30363d"),
    yaxis = dict(gridcolor="#21262d", linecolor="#30363d"),
)
MARGIN = dict(l=30, r=30, t=50, b=30)


def _dark(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(**DARK, margin=MARGIN, title=dict(text=title, font=dict(size=16)))
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 1. Which country has hosted the most T20I matches?
# ══════════════════════════════════════════════════════════════════════════════
def analysis_host_countries(matches: pd.DataFrame, top_n: int = 15):
    import plotly.express as px
    
    # ── Column name detect karo ──────────────────────────────────────────────
    # Try different possible column names
    possible_cols = [
        "Match Venue (Country)",   # original CSV column
        "host_country",            # t20_loader derived column
        "venue",                   # fallback
    ]
    
    col = None
    for c in possible_cols:
        if c in matches.columns:
            col = c
            break
    
    if col is None:
        return pd.DataFrame(), None
    
    # ── Count karo ───────────────────────────────────────────────────────────
    counts = (
        matches[col]
        .value_counts()
        .nlargest(top_n)
        .reset_index()
    )
    counts.columns = ["country", "matches"]
    
    # ── Plot ─────────────────────────────────────────────────────────────────
    fig = px.bar(
        counts, x="country", y="matches",
        color="matches", color_continuous_scale="Reds",
        text="matches",
        labels={"country": "Country", "matches": "Matches Hosted"},
        title=f"Top {top_n} Countries by T20I Matches Hosted",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        plot_bgcolor="#161b22", paper_bgcolor="#0d1117",
        font_color="#e6edf3",
        xaxis_tickangle=-45,
        margin=dict(l=20, r=20, t=40, b=100),
        showlegend=False,
    )
    
    return counts, fig 
# ══════════════════════════════════════════════════════════════════════════════
# Venue Analysis
# ══════════════════════════════════════════════════════════════════════════════

def analysis_venue(matches: pd.DataFrame,
                   selected_venue: str = None) -> tuple[pd.DataFrame, dict, list]:
    """
    Venue-wise analysis for T20Is.

    Returns:
        summary_df  -> DataFrame with all venues + metrics
        venue_stats -> dict with stats for selected venue
        figs        -> list of Plotly figures
    """

    # ── Column mapping ────────────────────────────────────────────
    stadium_col  = next((c for c in ("Match Venue (Stadium)", "venue", "stadium") if c in matches.columns), None)
    city_col     = next((c for c in ("Match Venue (City)", "city")                if c in matches.columns), None)
    country_col  = next((c for c in ("Match Venue (Country)", "country")          if c in matches.columns), None)
    t1_runs_col  = next((c for c in ("Team1 Runs Scored", "team1_runs")           if c in matches.columns), None)
    t2_runs_col  = next((c for c in ("Team2 Runs Scored", "team2_runs")           if c in matches.columns), None)
    toss_col     = next((c for c in ("Toss Winner", "toss_winner")                if c in matches.columns), None)
    toss_choice  = next((c for c in ("Toss Winner Choice", "toss_choice")         if c in matches.columns), None)
    winner_col   = next((c for c in ("Match Winner", "winner")                    if c in matches.columns), None)
    t1_col       = next((c for c in ("Team1 Name", "team1")                       if c in matches.columns), None)
    t2_col       = next((c for c in ("Team2 Name", "team2")                       if c in matches.columns), None)
    mid_col      = next((c for c in ("Match ID", "match_id")                      if c in matches.columns), None)

    if not stadium_col or not t1_runs_col or not t2_runs_col:
        return pd.DataFrame(), {}, []

    df = matches.copy()

    # ── Numeric conversion ────────────────────────────────────────
    df[t1_runs_col] = pd.to_numeric(df[t1_runs_col], errors="coerce")
    df[t2_runs_col] = pd.to_numeric(df[t2_runs_col], errors="coerce")

    # ── Toss winner chose bat → Team1 batted first ─────────────────
    # 1st innings = team that batted first
    # If toss winner chose "bat" → toss winner is team1 (batted first)
    # We treat Team1 runs = 1st innings, Team2 runs = 2nd innings
    # (assumption: data already structured this way)

    # ── Chasing win: team batting 2nd won ─────────────────────────
    if winner_col and t2_col:
        df["chase_win"] = (df[winner_col] == df[t2_col]).astype(int)
    else:
        df["chase_win"] = np.nan

    # ── Toss impact: toss winner won the match ────────────────────
    if toss_col and winner_col:
        df["toss_win_match"] = (df[toss_col] == df[winner_col]).astype(int)
    else:
        df["toss_win_match"] = np.nan

    # ── Aggregate per venue ───────────────────────────────────────
    agg = {}
    agg["matches"]       = (mid_col or t1_runs_col, "count")
    agg["avg_1st"]       = (t1_runs_col, "mean")
    agg["avg_2nd"]       = (t2_runs_col, "mean")
    agg["highest"]       = (t1_runs_col, "max")
    agg["lowest"]        = (t1_runs_col, "min")
    if "chase_win"       in df.columns: agg["chase_wins"] = ("chase_win", "sum")
    if "toss_win_match"  in df.columns: agg["toss_wins"]  = ("toss_win_match", "sum")

    venue_df = (
        df.groupby(stadium_col)
        .agg(**{k: v for k, v in agg.items()})
        .reset_index()
        .rename(columns={stadium_col: "venue"})
    )

    # ── Derived metrics ───────────────────────────────────────────
    venue_df["avg_1st"]    = venue_df["avg_1st"].round(1)
    venue_df["avg_2nd"]    = venue_df["avg_2nd"].round(1)
    venue_df["highest"]    = venue_df["highest"].astype(int)
    venue_df["lowest"]     = venue_df["lowest"].astype(int)

    if "chase_wins" in venue_df.columns:
        venue_df["chase_win_pct"] = (
            venue_df["chase_wins"] / venue_df["matches"] * 100
        ).round(1)

    if "toss_wins" in venue_df.columns:
        venue_df["toss_impact_pct"] = (
            venue_df["toss_wins"] / venue_df["matches"] * 100
        ).round(1)

    venue_df = venue_df.sort_values("matches", ascending=False).reset_index(drop=True)

    # ── Add city/country if available ────────────────────────────
    if city_col:
        city_map = df.groupby(stadium_col)[city_col].first().to_dict()
        venue_df["city"] = venue_df["venue"].map(city_map)
    if country_col:
        country_map = df.groupby(stadium_col)[country_col].first().to_dict()
        venue_df["country"] = venue_df["venue"].map(country_map)

    # ── Stats for selected venue ──────────────────────────────────
    venue_stats = {}
    if selected_venue and selected_venue in venue_df["venue"].values:
        row = venue_df[venue_df["venue"] == selected_venue].iloc[0]
        venue_stats = {
            "matches":        int(row["matches"]),
            "highest":        int(row["highest"]),
            "lowest":         int(row["lowest"]),
            "avg_1st":        float(row["avg_1st"]),
            "avg_2nd":        float(row["avg_2nd"]),
            "chase_win_pct":  float(row.get("chase_win_pct", 0)),
            "toss_impact_pct":float(row.get("toss_impact_pct", 0)),
        }

    # ── Figures ───────────────────────────────────────────────────
   # ── Figures ───────────────────────────────────────────────────
    figs = []
    top15 = venue_df.head(15)

    # Fig 1: Avg 1st vs 2nd innings — Grouped Bar (same as before, good che)
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        name="Avg 1st Innings",
        x=top15["venue"], y=top15["avg_1st"],
        marker_color="#378ADD", text=top15["avg_1st"],
        textposition="outside",
    ))
    fig1.add_trace(go.Bar(
        name="Avg 2nd Innings",
        x=top15["venue"], y=top15["avg_2nd"],
        marker_color="#D85A30", text=top15["avg_2nd"],
        textposition="outside",
    ))
    fig1.update_layout(
        barmode="group",
        title={"text": "Avg 1st vs 2nd Innings Score by Venue", "x": 0.5},
        xaxis_tickangle=-45,
        plot_bgcolor="#161b22", paper_bgcolor="#0d1117",
        font_color="#e6edf3",
        legend=dict(orientation="h", y=1.1),
        margin=dict(l=20, r=20, t=60, b=120),
        height=520,
    )
    figs.append(fig1)

    # Fig 2: Chasing Win % — Horizontal bar with color zones
    if "chase_win_pct" in venue_df.columns:
        chase_df = top15.sort_values("chase_win_pct", ascending=True)
        
        # Color: >55 = green (batting second easy), <45 = red (batting first easy), else yellow
        colors = []
        for val in chase_df["chase_win_pct"]:
            if val >= 55:
                colors.append("#1D9E75")   # green
            elif val <= 45:
                colors.append("#D85A30")   # red
            else:
                colors.append("#EF9F27")   # amber

        fig2 = go.Figure(go.Bar(
            x=chase_df["chase_win_pct"],
            y=chase_df["venue"],
            orientation="h",
            marker_color=colors,
            text=[f"{v}%" for v in chase_df["chase_win_pct"]],
            textposition="outside",
        ))
        # 50% reference line
        fig2.add_vline(
            x=50, line_dash="dash",
            line_color="#888780", line_width=1.5,
            annotation_text="50% mark",
            annotation_position="top",
            annotation_font_color="#888780",
        )
        fig2.update_layout(
            title={"text": "🏃 Chasing Win % by Venue", "x": 0.5},
            xaxis=dict(title="Chasing Win %", range=[0, 80]),
            yaxis=dict(title=""),
            plot_bgcolor="#161b22", paper_bgcolor="#0d1117",
            font_color="#e6edf3",
            margin=dict(l=20, r=60, t=50, b=20),
            height=520,
            showlegend=False,
        )
        figs.append(fig2)

    # Fig 3: Toss Impact — Dot/Lollipop chart
    if "toss_impact_pct" in venue_df.columns:
        toss_df = top15.sort_values("toss_impact_pct", ascending=True)

        fig3 = go.Figure()

        # Stem lines (50% thhi actual value sudhi)
        for i, row in toss_df.iterrows():
            fig3.add_shape(
                type="line",
                x0=50, x1=row["toss_impact_pct"],
                y0=row["venue"], y1=row["venue"],
                line=dict(
                    color="#1D9E75" if row["toss_impact_pct"] >= 50 else "#D85A30",
                    width=2,
                ),
            )

        # Dots
        fig3.add_trace(go.Scatter(
            x=toss_df["toss_impact_pct"],
            y=toss_df["venue"],
            mode="markers+text",
            marker=dict(
                size=14,
                color=["#1D9E75" if v >= 50 else "#D85A30"
                       for v in toss_df["toss_impact_pct"]],
                line=dict(width=1, color="#0d1117"),
            ),
            text=[f"{v}%" for v in toss_df["toss_impact_pct"]],
            textposition="middle right",
            textfont=dict(size=11),
        ))

        # 50% reference line
        fig3.add_vline(
            x=50, line_dash="dash",
            line_color="#888780", line_width=1.5,
            annotation_text="50% (random chance)",
            annotation_position="top",
            annotation_font_color="#888780",
        )
        fig3.update_layout(
            title={"text": "🪙 Toss Impact % by Venue", "x": 0.5},
            xaxis=dict(title="Toss Winner = Match Winner %", range=[25, 75]),
            yaxis=dict(title=""),
            plot_bgcolor="#161b22", paper_bgcolor="#0d1117",
            font_color="#e6edf3",
            margin=dict(l=20, r=80, t=50, b=20),
            height=520,
            showlegend=False,
        )
        figs.append(fig3)

    return venue_df, venue_stats, figs
# ══════════════════════════════════════════════════════════════════════════════
# 2. Top 10 players with most Man-of-the-Match awards
# ══════════════════════════════════════════════════════════════════════════════

def analysis_man_of_match(matches: pd.DataFrame, 
                           players: pd.DataFrame,
                           top_n: int = 10) -> tuple[pd.DataFrame, go.Figure]:
    """
    Top T20I Man-of-the-Match winners.

    Returns:
        df  -> DataFrame with [player, awards]
        fig -> Plotly Figure
    """

    # Possible MOM columns
    for col in ("man_of_match", "MOM Player", "MOM Player 1",
                "mom_player_id", "Match Winner"):

        if col in matches.columns:
            mom_col = col
            break
    else:
        return pd.DataFrame(), go.Figure()

    # -------------------------------------------------------
    # Grouping & counting awards (same logic as your seaborn code)
    # -------------------------------------------------------
    motm_players = (
        matches.groupby(mom_col)[['match_id']]
        .count()
        .rename(columns={'match_id': 'awards'})
        .reset_index()
    )

    # Rename MOM column to player
    motm_players.rename(columns={mom_col: 'player'}, inplace=True)

    # -------------------------------------------------------
    # Merge with player info if player IDs are present
    # -------------------------------------------------------
    if ("player_id" in players.columns and 
        "player_name" in players.columns):

        try:
            motm_players = motm_players.merge(
                players[['player_id', 'player_name']],
                left_on='player',
                right_on='player_id',
                how='left'
            )

            # Use player_name if available
            motm_players['player'] = (
                motm_players['player_name']
                .fillna(motm_players['player'].astype(str))
            )

        except:
            pass

    # -------------------------------------------------------
    # Top N players
    # -------------------------------------------------------
    motm_players = (
        motm_players[['player', 'awards']]
        .sort_values(by='awards', ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    # -------------------------------------------------------
    # Plotly Chart
    # -------------------------------------------------------
    fig = px.bar(
        motm_players,
        x='player',
        y='awards',
        color='awards',
        color_continuous_scale='Viridis',
        text='awards'
    )

    # Customizations
    fig.update_traces(
        textposition='inside',
        textfont=dict(color='white', size=12)
    )

    fig.update_layout(
        title={
            'text': "🏅 Top 10 Players with Most Man of the Match Awards",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title='Players',
        yaxis_title='No. of Awards',
        xaxis_tickangle=-45,
        template='plotly_dark',
        height=550
    )

    return motm_players, fig

# ══════════════════════════════════════════════════════════════════════════════
# 3. Highest wicket-takers in T20 Internationals
# ══════════════════════════════════════════════════════════════════════════════

def analysis_wicket_takers(bowling: pd.DataFrame,
                            players: pd.DataFrame,
                            top_n: int = 10) -> tuple[pd.DataFrame, go.Figure]:
    """
    Aggregates bowling card to find highest wicket-takers.

    Returns (df, fig) where df has columns:
      [player, wickets, matches, runs_conceded, overs, economy]
    """
    # Determine bowler identifier column
    name_col = None
    for c in ("bowler_name", "bowler_id"):
        if c in bowling.columns:
            name_col = c
            break
    if name_col is None:
        return pd.DataFrame(), go.Figure()

    # Merge player names if we have IDs
    if (name_col == "bowler_id"
            and "player_id" in players.columns
            and "player_name" in players.columns):
        id_map = players.set_index("player_id")["player_name"].to_dict()
        bowling = bowling.copy()
        bowling["bowler_display"] = (
            bowling["bowler_id"].map(id_map).fillna(bowling["bowler_id"].astype(str))
        )
        name_col = "bowler_display"

    agg_cols = {}
    if "wickets"       in bowling.columns: agg_cols["wickets"]       = ("wickets",       "sum")
    if "match_id"      in bowling.columns: agg_cols["matches"]       = ("match_id",      "nunique")
    if "runs_conceded" in bowling.columns: agg_cols["runs_conceded"] = ("runs_conceded", "sum")
    if "overs"         in bowling.columns: agg_cols["overs"]         = ("overs",         "sum")

    df = (
        bowling.groupby(name_col)
        .agg(**agg_cols)
        .reset_index()
        .rename(columns={name_col: "player"})
    )

    if "runs_conceded" in df.columns and "overs" in df.columns:
        df["economy"] = (
            df["runs_conceded"] / df["overs"].replace(0, np.nan)
        ).round(2)

    df = df.sort_values("wickets", ascending=False).head(top_n).reset_index(drop=True)

    fig = px.bar(
        df, x="wickets", y="player", orientation="h",
        color="wickets", color_continuous_scale="Reds",
        labels={"wickets": "Wickets", "player": "Bowler"},
        text="wickets",
        hover_data=[c for c in ["matches", "economy", "runs_conceded"] if c in df.columns],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis=dict(autorange="reversed"))
    _dark(fig, "🎯 Highest Wicket-Takers in T20 Internationals")
    return df, fig


# ══════════════════════════════════════════════════════════════════════════════
# 4. Highest run-scorers in T20 Internationals
# ══════════════════════════════════════════════════════════════════════════════

def analysis_run_scorers(batting: pd.DataFrame,
                          players: pd.DataFrame,
                          top_n: int = 10) -> tuple[pd.DataFrame, go.Figure]:
    """
    Aggregates batting card to find highest run-scorers.

    Returns (df, fig) where df has columns:
      [player, runs, balls, matches, sixes, fours, strike_rate]
    """
    name_col = None
    for c in ("batsman_name", "batsman_id"):
        if c in batting.columns:
            name_col = c
            break
    if name_col is None:
        return pd.DataFrame(), go.Figure()

    if (name_col == "batsman_id"
            and "player_id" in players.columns
            and "player_name" in players.columns):
        id_map = players.set_index("player_id")["player_name"].to_dict()
        batting = batting.copy()
        batting["batsman_display"] = (
            batting["batsman_id"].map(id_map).fillna(batting["batsman_id"].astype(str))
        )
        name_col = "batsman_display"

    agg_cols = {}
    if "runs"     in batting.columns: agg_cols["runs"]    = ("runs",     "sum")
    if "balls"    in batting.columns: agg_cols["balls"]   = ("balls",    "sum")
    if "match_id" in batting.columns: agg_cols["matches"] = ("match_id", "nunique")
    if "sixes"    in batting.columns: agg_cols["sixes"]   = ("sixes",    "sum")
    if "fours"    in batting.columns: agg_cols["fours"]   = ("fours",    "sum")

    df = (
        batting.groupby(name_col)
        .agg(**agg_cols)
        .reset_index()
        .rename(columns={name_col: "player"})
    )

    if "runs" in df.columns and "balls" in df.columns:
        df["strike_rate"] = (
            df["runs"] / df["balls"].replace(0, np.nan) * 100
        ).round(2)

    df = df.sort_values("runs", ascending=False).head(top_n).reset_index(drop=True)

    fig = px.bar(
        df, x="runs", y="player", orientation="h",
        color="strike_rate" if "strike_rate" in df.columns else "runs",
        color_continuous_scale="Oranges",
        labels={"runs": "Total Runs", "player": "Batsman", "strike_rate": "Strike Rate"},
        text="runs",
        hover_data=[c for c in ["matches", "sixes", "fours", "strike_rate"] if c in df.columns],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(yaxis=dict(autorange="reversed"))
    _dark(fig, "🏏 Highest Run-Scorers in T20 Internationals")
    return df, fig

# ══════════════════════════════════════════════════════════════════════════════
# 6. Who hit the most fours?
# ══════════════════════════════════════════════════════════════════════════════

def analysis_most_fours(batting: pd.DataFrame,
                         players: pd.DataFrame,
                         top_n: int = 10) -> tuple[pd.DataFrame, go.Figure]:
    """
    Players with most fours in T20 Internationals.

    Returns (df, fig) where df has columns [player, fours, (matches)].
    """
    if "fours" not in batting.columns:
        return pd.DataFrame(), go.Figure()

    name_col = None
    for c in ("batsman_name", "batsman_id"):
        if c in batting.columns:
            name_col = c
            break
    if name_col is None:
        return pd.DataFrame(), go.Figure()

    if (name_col == "batsman_id"
            and "player_id" in players.columns
            and "player_name" in players.columns):
        id_map = players.set_index("player_id")["player_name"].to_dict()
        batting = batting.copy()
        batting["batsman_display"] = (
            batting["batsman_id"].map(id_map).fillna(batting["batsman_id"].astype(str))
        )
        name_col = "batsman_display"

    agg_cols = {"fours": ("fours", "sum")}
    if "match_id" in batting.columns:
        agg_cols["matches"] = ("match_id", "nunique")

    df = (
        batting.groupby(name_col)
        .agg(**agg_cols)
        .reset_index()
        .rename(columns={name_col: "player"})
        .sort_values("fours", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    fig = px.bar(
        df, x="player", y="fours",
        color="fours", color_continuous_scale="Blues",
        labels={"fours": "Fours", "player": "Player"},
        text="fours",
    )
    fig.update_traces(textposition="outside")
    _dark(fig, "🏏 Who Hit the Most Fours in T20Is?")
    return df, fig


# ══════════════════════════════════════════════════════════════════════════════
# Bonus: team-level fours analysis
# ══════════════════════════════════════════════════════════════════════════════

def analysis_team_fours(batting: pd.DataFrame,
                         top_n: int = 10) -> tuple[pd.DataFrame, go.Figure]:
    """Fours hit per team (not per player)."""
    if "fours" not in batting.columns or "team" not in batting.columns:
        return pd.DataFrame(), go.Figure()

    df = (
        batting.groupby("team")["fours"]
        .sum()
        .reset_index()
        .sort_values("fours", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    fig = px.pie(
        df, names="team", values="fours",
        color_discrete_sequence=px.colors.qualitative.Bold,
        hole=0.35,
    )
    fig.update_traces(texttemplate="%{label}<br>%{value}", textinfo="label+value")
    _dark(fig, "🏏 Fours Per Team in T20Is")
    return df, fig
# ══════════════════════════════════════════════════════════════════════════════
# 5. Who hit the most sixes?
# ══════════════════════════════════════════════════════════════════════════════

def analysis_most_sixes(batting: pd.DataFrame,
                         players: pd.DataFrame,
                         top_n: int = 10) -> tuple[pd.DataFrame, go.Figure]:
    """
    Players with most sixes in T20 Internationals.

    Returns (df, fig) where df has columns [player, sixes, (matches)].
    """
    if "sixes" not in batting.columns:
        return pd.DataFrame(), go.Figure()

    name_col = None
    for c in ("batsman_name", "batsman_id"):
        if c in batting.columns:
            name_col = c
            break
    if name_col is None:
        return pd.DataFrame(), go.Figure()

    if (name_col == "batsman_id"
            and "player_id" in players.columns
            and "player_name" in players.columns):
        id_map = players.set_index("player_id")["player_name"].to_dict()
        batting = batting.copy()
        batting["batsman_display"] = (
            batting["batsman_id"].map(id_map).fillna(batting["batsman_id"].astype(str))
        )
        name_col = "batsman_display"

    agg_cols = {"sixes": ("sixes", "sum")}
    if "match_id" in batting.columns:
        agg_cols["matches"] = ("match_id", "nunique")

    df = (
        batting.groupby(name_col)
        .agg(**agg_cols)
        .reset_index()
        .rename(columns={name_col: "player"})
        .sort_values("sixes", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    fig = px.bar(
        df, x="player", y="sixes",
        color="sixes", color_continuous_scale="Greens",
        labels={"sixes": "Sixes", "player": "Player"},
        text="sixes",
    )
    fig.update_traces(textposition="outside")
    _dark(fig, "💥 Who Hit the Most Sixes in T20Is?")
    return df, fig


# ══════════════════════════════════════════════════════════════════════════════
# Most Successful Teams in T20Is
# ══════════════════════════════════════════════════════════════════════════════

def analysis_successful_teams(matches: pd.DataFrame,
                              top_n: int = 10) -> tuple[pd.DataFrame, go.Figure]:

    # ----------------------------------------------------------------
    # Detect Winner Column
    # ----------------------------------------------------------------
    for col in ("Match Winner", "winner", "match_winner",
                "Winning Team", "Winner"):

        if col in matches.columns:
            winner_col = col
            break
    else:
        return pd.DataFrame(), go.Figure()

    # ----------------------------------------------------------------
    # Group by Match Winner & Count Wins
    # ----------------------------------------------------------------
    wins_df = (
        matches.groupby(winner_col)[['match_id']]
        .count()
        .rename(columns={'match_id': 'matches_won'})
        .reset_index()
    )

    # Rename winner column → team
    wins_df.rename(columns={winner_col: 'team'}, inplace=True)

    # ----------------------------------------------------------------
    # Top N Teams
    # ----------------------------------------------------------------
    top_teams = (
        wins_df
        .sort_values(by='matches_won', ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    # Reverse order for horizontal ranking
    top_teams = top_teams.iloc[::-1]

    # ----------------------------------------------------------------
    # Plotly Bar Chart
    # ----------------------------------------------------------------
    fig = px.bar(
        top_teams,
        x='matches_won',
        y='team',
        orientation='h',
        color='matches_won',
        color_continuous_scale='magma',
        text='matches_won'
    )

    # ----------------------------------------------------------------
    # Styling
    # ----------------------------------------------------------------
    fig.update_traces(
        textposition='inside',
        insidetextanchor='end',
        textfont=dict(
            size=16,
            color='white'
        )
    )

    fig.update_layout(
        title=dict(
            text="Most succesful teams in T20Is",
            x=0.5,
            font=dict(size=24)
        ),

        xaxis=dict(
            title="Matches won",
            title_font=dict(size=18),
            tickfont=dict(size=13),
            showgrid=True,
        ),

        yaxis=dict(
            title="Teams",
            title_font=dict(size=18),
            tickfont=dict(size=14)
        ),

        template="plotly_dark",
        height=600,

        margin=dict(
            l=40,
            r=40,
            t=80,
            b=40
        ),

        coloraxis_showscale=False
    )

    return top_teams[::-1], fig

# ══════════════════════════════════════════════════════════════════════════════
# Bonus: team-level sixes analysis (used in Streamlit T20 Rankings tab)
# ══════════════════════════════════════════════════════════════════════════════

def analysis_team_sixes(batting: pd.DataFrame,
                         top_n: int = 10) -> tuple[pd.DataFrame, go.Figure]:
    """Sixes hit per team (not per player)."""
    if "sixes" not in batting.columns or "team" not in batting.columns:
        return pd.DataFrame(), go.Figure()

    df = (
        batting.groupby("team")["sixes"]
        .sum()
        .reset_index()
        .sort_values("sixes", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

    fig = px.pie(
        df, names="team", values="sixes",
        color_discrete_sequence=px.colors.qualitative.Bold,
        hole=0.35,
    )
    fig.update_traces(texttemplate="%{label}<br>%{value}", textinfo="label+value")
    _dark(fig, "💥 Sixes Per Team in T20Is")
    return df, fig


def analysis_head_to_head(matches: pd.DataFrame,
                           players: pd.DataFrame,
                           team_a: str,
                           team_b: str) -> tuple[pd.DataFrame, dict]:
    """
    Head-to-Head analysis between two teams.

    Returns:
        df    -> DataFrame of all H2H matches (sorted newest first)
        stats -> dict with summary metrics
    """
    # Detect team columns
    t1_col, t2_col = None, None
    for c in ("Team1 Name", "team1", "team1_name"):
        if c in matches.columns: t1_col = c; break
    for c in ("Team2 Name", "team2", "team2_name"):
        if c in matches.columns: t2_col = c; break

    # Detect winner column
    win_col = None
    for c in ("Match Winner", "winner", "match_winner"):
        if c in matches.columns: win_col = c; break

    if not all([t1_col, t2_col, win_col]):
        return pd.DataFrame(), {}

    # Filter H2H matches
    mask = (
        ((matches[t1_col] == team_a) & (matches[t2_col] == team_b)) |
        ((matches[t1_col] == team_b) & (matches[t2_col] == team_a))
    )
    df = matches[mask].copy()

    if df.empty:
        return df, {}

    total   = len(df)
    wins_a  = (df[win_col] == team_a).sum()
    wins_b  = (df[win_col] == team_b).sum()
    draws   = total - wins_a - wins_b

    # Highest score
    score_cols = [c for c in ("Team1 Runs Scored", "Team2 Runs Scored",
                               "team1_runs", "team2_runs") if c in df.columns]
    highest = int(df[score_cols].max().max()) if score_cols else None

    # Sort newest first (detect date column)
    for d_col in ("Match Date", "date", "match_date"):
        if d_col in df.columns:
            df = df.sort_values(d_col, ascending=False)
            break

    stats = {
        "total":   total,
        "wins_a":  int(wins_a),
        "wins_b":  int(wins_b),
        "draws":   int(draws),
        "pct_a":   round(wins_a / total * 100, 1),
        "pct_b":   round(wins_b / total * 100, 1),
        "highest": highest,
    }
    return df, stats


# ══════════════════════════════════════════════════════════════════════════════
# PLAYER CAREER ARC  –  paste this into t20_analysis.py
# ══════════════════════════════════════════════════════════════════════════════

def analysis_career_arc(
    batting:  pd.DataFrame,
    bowling:  pd.DataFrame,
    players:  pd.DataFrame,
    matches:  pd.DataFrame,
    player_name: str,
    mode: str = "batting",   # "batting" | "bowling"
) -> tuple[pd.DataFrame, list]:
    """
    Player Career Arc  –  season-by-season batting OR bowling stats.

    Parameters
    ----------
    batting      : t20i_Batting_Card   DataFrame
    bowling      : t20i_Bowling_Card   DataFrame
    players      : players_info        DataFrame
    matches      : t20i_Matches_Data   DataFrame  (needs 'Match Date' / 'date')
    player_name  : exact player name string
    mode         : "batting" or "bowling"

    Returns
    -------
    arc_df  ->  DataFrame with one row per season
    figs    ->  list of two Plotly figures  [main_fig, sub_fig]
    """

    # ── 1. Resolve player_id from name ──────────────────────────────────────
    pid = None
    if "player_name" in players.columns and "player_id" in players.columns:
        row = players[players["player_name"].str.strip() == player_name.strip()]
        if not row.empty:
            pid = row.iloc[0]["player_id"]

    # ── 2. Attach season (year) to matches ──────────────────────────────────
    date_col = next(
        (c for c in ("Match Date", "date", "match_date") if c in matches.columns),
        None,
    )
    mid_col = next(
        (c for c in ("Match ID", "match_id") if c in matches.columns),
        None,
    )

    if date_col and mid_col:
        match_season = matches[[mid_col, date_col]].copy()
        match_season[date_col] = pd.to_datetime(match_season[date_col], errors="coerce")
        match_season["season"] = match_season[date_col].dt.year
        match_season = match_season.rename(columns={mid_col: "match_id"})
    else:
        match_season = pd.DataFrame(columns=["match_id", "season"])

    # ── 3. Build arc_df ──────────────────────────────────────────────────────
    if mode == "batting":
        arc_df, figs = _batting_arc(batting, players, match_season, player_name, pid)
    else:
        arc_df, figs = _bowling_arc(bowling, players, match_season, player_name, pid)

    return arc_df, figs


# ── helpers ──────────────────────────────────────────────────────────────────

def _resolve_name_col(df: pd.DataFrame, id_col: str, players: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Map player_id → player_name if needed; return (df, name_col)."""
    if id_col in df.columns:
        if "player_id" in players.columns and "player_name" in players.columns:
            id_map = players.set_index("player_id")["player_name"].to_dict()
            df = df.copy()
            df["_display"] = df[id_col].map(id_map).fillna(df[id_col].astype(str))
            return df, "_display"
        return df, id_col

    name_col = next((c for c in ("batsman_name", "bowler_name", "player_name") if c in df.columns), None)
    return df, name_col


def _attach_season(df: pd.DataFrame, match_season: pd.DataFrame) -> pd.DataFrame:
    """Left-join season year onto a card DataFrame."""
    if match_season.empty or "match_id" not in df.columns:
        return df
    return df.merge(match_season[["match_id", "season"]], on="match_id", how="left")


def _batting_arc(
    batting: pd.DataFrame,
    players: pd.DataFrame,
    match_season: pd.DataFrame,
    player_name: str,
    pid,
) -> tuple[pd.DataFrame, list]:

    id_col = next((c for c in ("batsman_id", "batsman_name") if c in batting.columns), None)
    if id_col is None:
        return pd.DataFrame(), []

    df, name_col = _resolve_name_col(batting, id_col, players)
    if name_col is None:
        return pd.DataFrame(), []

    df = df[df[name_col].astype(str).str.strip() == player_name.strip()].copy()
    if df.empty:
        return pd.DataFrame(), []

    df = _attach_season(df, match_season)
    if "season" not in df.columns or df["season"].isna().all():
        return pd.DataFrame(), []

    df["runs"]  = pd.to_numeric(df.get("runs",  0), errors="coerce").fillna(0)
    df["balls"] = pd.to_numeric(df.get("balls", 0), errors="coerce").fillna(0)
    df["sixes"] = pd.to_numeric(df.get("sixes", 0), errors="coerce").fillna(0)
    df["fours"] = pd.to_numeric(df.get("fours", 0), errors="coerce").fillna(0)

    agg = (
        df.groupby("season")
        .agg(
            runs    = ("runs",     "sum"),
            balls   = ("balls",    "sum"),
            sixes   = ("sixes",    "sum"),
            fours   = ("fours",    "sum"),
            matches = ("match_id", "nunique") if "match_id" in df.columns else ("runs", "count"),
        )
        .reset_index()
        .sort_values("season")
    )
    agg["strike_rate"] = (agg["runs"] / agg["balls"].replace(0, np.nan) * 100).round(1)
    agg["avg_per_match"] = (agg["runs"] / agg["matches"].replace(0, np.nan)).round(1)

    peak_idx = agg["runs"].idxmax()

    # ── Fig 1: Runs per season (line + area) ────────────────────────────────
    colors = ["#378ADD"] * len(agg)
    colors[agg.index.get_loc(peak_idx)] = "#EF9F27"

    fig1 = go.Figure()

    # Area fill
    fig1.add_trace(go.Scatter(
        x=agg["season"], y=agg["runs"],
        mode="none", fill="tozeroy",
        fillcolor="rgba(55,138,221,0.12)",
        showlegend=False, hoverinfo="skip",
    ))

    # Line
    fig1.add_trace(go.Scatter(
        x=agg["season"], y=agg["runs"],
        mode="lines+markers+text",
        line=dict(color="#378ADD", width=2.5),
        marker=dict(
            color=colors,
            size=[10 if i == agg.index.get_loc(peak_idx) else 6 for i in range(len(agg))],
            line=dict(width=1.5, color="#0d1117"),
        ),
        text=agg["runs"],
        textposition="top center",
        textfont=dict(size=10),
        name="Runs",
        customdata=np.stack([agg["strike_rate"], agg["matches"], agg["sixes"], agg["fours"]], axis=1),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Runs: %{y}<br>"
            "Strike Rate: %{customdata[0]}<br>"
            "Matches: %{customdata[1]}<br>"
            "Sixes: %{customdata[2]}  Fours: %{customdata[3]}"
            "<extra></extra>"
        ),
    ))

    # Peak annotation
    peak_row = agg.loc[peak_idx]
    fig1.add_annotation(
        x=peak_row["season"], y=peak_row["runs"],
        text=f"Peak {int(peak_row['season'])}",
        showarrow=True, arrowhead=2, arrowcolor="#EF9F27",
        font=dict(color="#EF9F27", size=11),
        bgcolor="#0d1117", bordercolor="#EF9F27", borderwidth=1,
        ay=-36, ax=0,
    )

    fig1.update_layout(
        title=dict(text=f"🏏 {player_name} — Batting Career Arc (T20I)", x=0.5, font=dict(size=16)),
        xaxis=dict(title="Season", dtick=1, tickangle=-45, gridcolor="#21262d", linecolor="#30363d"),
        yaxis=dict(title="Runs", gridcolor="#21262d", linecolor="#30363d"),
        plot_bgcolor="#161b22", paper_bgcolor="#0d1117",
        font_color="#e6edf3",
        showlegend=False,
        margin=dict(l=40, r=40, t=60, b=60),
        height=420,
    )

    # ── Fig 2: Strike Rate per season (bar) ──────────────────────────────────
    sr_colors = [
        "#1D9E75" if v >= 145 else "#EF9F27" if v >= 130 else "#D85A30"
        for v in agg["strike_rate"].fillna(0)
    ]

    fig2 = go.Figure(go.Bar(
        x=agg["season"], y=agg["strike_rate"],
        marker_color=sr_colors,
        text=agg["strike_rate"],
        textposition="outside",
        textfont=dict(size=10),
        name="Strike Rate",
        hovertemplate="<b>%{x}</b><br>Strike Rate: %{y}<extra></extra>",
    ))

    # 130 reference line
    fig2.add_hline(
        y=130, line_dash="dash", line_color="#888780", line_width=1.2,
        annotation_text="SR 130", annotation_font_color="#888780",
        annotation_position="bottom right",
    )

    fig2.update_layout(
        title=dict(text="Strike Rate per Season", x=0.5, font=dict(size=14)),
        xaxis=dict(dtick=1, tickangle=-45, gridcolor="#21262d", linecolor="#30363d"),
        yaxis=dict(title="Strike Rate", gridcolor="#21262d", linecolor="#30363d", range=[100, agg["strike_rate"].max() + 15]),
        plot_bgcolor="#161b22", paper_bgcolor="#0d1117",
        font_color="#e6edf3",
        showlegend=False,
        margin=dict(l=40, r=40, t=50, b=60),
        height=320,
    )

    return agg, [fig1, fig2]


def _bowling_arc(
    bowling: pd.DataFrame,
    players: pd.DataFrame,
    match_season: pd.DataFrame,
    player_name: str,
    pid,
) -> tuple[pd.DataFrame, list]:

    id_col = next((c for c in ("bowler_id", "bowler_name") if c in bowling.columns), None)
    if id_col is None:
        return pd.DataFrame(), []

    df, name_col = _resolve_name_col(bowling, id_col, players)
    if name_col is None:
        return pd.DataFrame(), []

    df = df[df[name_col].astype(str).str.strip() == player_name.strip()].copy()
    if df.empty:
        return pd.DataFrame(), []

    df = _attach_season(df, match_season)
    if "season" not in df.columns or df["season"].isna().all():
        return pd.DataFrame(), []

    df["wickets"]       = pd.to_numeric(df.get("wickets",       0), errors="coerce").fillna(0)
    df["runs_conceded"] = pd.to_numeric(df.get("conceded",      df.get("runs_conceded", 0)), errors="coerce").fillna(0)
    df["overs"]         = pd.to_numeric(df.get("overs",         0), errors="coerce").fillna(0)

    agg = (
        df.groupby("season")
        .agg(
            wickets       = ("wickets",       "sum"),
            runs_conceded = ("runs_conceded", "sum"),
            overs         = ("overs",         "sum"),
            matches       = ("match_id",      "nunique") if "match_id" in df.columns else ("wickets", "count"),
        )
        .reset_index()
        .sort_values("season")
    )
    agg["economy"]  = (agg["runs_conceded"] / agg["overs"].replace(0, np.nan)).round(2)
    agg["avg"]      = (agg["runs_conceded"] / agg["wickets"].replace(0, np.nan)).round(2)

    peak_idx = agg["wickets"].idxmax()

    # ── Fig 1: Wickets per season ────────────────────────────────────────────
    colors = ["#D85A30"] * len(agg)
    colors[agg.index.get_loc(peak_idx)] = "#EF9F27"

    fig1 = go.Figure()

    fig1.add_trace(go.Scatter(
        x=agg["season"], y=agg["wickets"],
        mode="none", fill="tozeroy",
        fillcolor="rgba(216,90,48,0.12)",
        showlegend=False, hoverinfo="skip",
    ))

    fig1.add_trace(go.Scatter(
        x=agg["season"], y=agg["wickets"],
        mode="lines+markers+text",
        line=dict(color="#D85A30", width=2.5),
        marker=dict(
            color=colors,
            size=[10 if i == agg.index.get_loc(peak_idx) else 6 for i in range(len(agg))],
            line=dict(width=1.5, color="#0d1117"),
        ),
        text=agg["wickets"],
        textposition="top center",
        textfont=dict(size=10),
        name="Wickets",
        customdata=np.stack([agg["economy"], agg["avg"], agg["matches"]], axis=1),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Wickets: %{y}<br>"
            "Economy: %{customdata[0]}<br>"
            "Average: %{customdata[1]}<br>"
            "Matches: %{customdata[2]}"
            "<extra></extra>"
        ),
    ))

    peak_row = agg.loc[peak_idx]
    fig1.add_annotation(
        x=peak_row["season"], y=peak_row["wickets"],
        text=f"Peak {int(peak_row['season'])}",
        showarrow=True, arrowhead=2, arrowcolor="#EF9F27",
        font=dict(color="#EF9F27", size=11),
        bgcolor="#0d1117", bordercolor="#EF9F27", borderwidth=1,
        ay=-36, ax=0,
    )

    fig1.update_layout(
        title=dict(text=f"🎯 {player_name} — Bowling Career Arc (T20I)", x=0.5, font=dict(size=16)),
        xaxis=dict(title="Season", dtick=1, tickangle=-45, gridcolor="#21262d", linecolor="#30363d"),
        yaxis=dict(title="Wickets", gridcolor="#21262d", linecolor="#30363d"),
        plot_bgcolor="#161b22", paper_bgcolor="#0d1117",
        font_color="#e6edf3",
        showlegend=False,
        margin=dict(l=40, r=40, t=60, b=60),
        height=420,
    )

    # ── Fig 2: Economy per season ────────────────────────────────────────────
    econ_colors = [
        "#1D9E75" if v <= 7.0 else "#EF9F27" if v <= 8.5 else "#D85A30"
        for v in agg["economy"].fillna(99)
    ]

    fig2 = go.Figure(go.Bar(
        x=agg["season"], y=agg["economy"],
        marker_color=econ_colors,
        text=agg["economy"],
        textposition="outside",
        textfont=dict(size=10),
        name="Economy",
        hovertemplate="<b>%{x}</b><br>Economy: %{y}<extra></extra>",
    ))

    fig2.add_hline(
        y=8.0, line_dash="dash", line_color="#888780", line_width=1.2,
        annotation_text="Econ 8.0", annotation_font_color="#888780",
        annotation_position="bottom right",
    )

    fig2.update_layout(
        title=dict(text="Economy Rate per Season", x=0.5, font=dict(size=14)),
        xaxis=dict(dtick=1, tickangle=-45, gridcolor="#21262d", linecolor="#30363d"),
        yaxis=dict(title="Economy", gridcolor="#21262d", linecolor="#30363d",
                   range=[0, agg["economy"].max() + 1.5]),
        plot_bgcolor="#161b22", paper_bgcolor="#0d1117",
        font_color="#e6edf3",
        showlegend=False,
        margin=dict(l=40, r=40, t=50, b=60),
        height=320,
    )

    return agg, [fig1, fig2]

# ══════════════════════════════════════════════════════════════════════════════
# PASTE THESE 3 FUNCTIONS AT THE BOTTOM OF  utils/t20_analysis.py
# ══════════════════════════════════════════════════════════════════════════════

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ══════════════════════════════════════════════════════════════════════════════
# A. BALL-BY-BALL HEATMAP
#    – Scoring zones (runs per phase/wicket bucket)
#    – Bowler delivery patterns (economy by over)
# ══════════════════════════════════════════════════════════════════════════════

def analysis_ball_heatmap(
    batting:  pd.DataFrame,
    bowling:  pd.DataFrame,
    players:  pd.DataFrame,
    matches:  pd.DataFrame,
    mode: str = "batting",       # "batting" | "bowling"
    player_name: str = None,     # None = all players (team-level)
    team: str = None,            # optional team filter
) -> tuple[pd.DataFrame, list]:
    """
    Ball-by-Ball Heatmap.

    Batting mode  → runs scored per (over_bucket × wickets_fallen) zone
    Bowling mode  → economy rate per (over × bowler) heatmap

    Returns
    -------
    heatmap_df  : pivot DataFrame used for the plot
    figs        : list of Plotly figures
    """

    # ── helper: detect column ─────────────────────────────────────────────────
    def _col(df, *names):
        return next((c for c in names if c in df.columns), None)

    figs = []

    # ── Attach season / match info ─────────────────────────────────────────────
    mid_col   = _col(matches, "Match ID", "match_id")
    date_col  = _col(matches, "Match Date", "date", "match_date")

    if mid_col and date_col:
        ms = matches[[mid_col, date_col]].copy()
        ms[date_col] = pd.to_datetime(ms[date_col], errors="coerce")
        ms["season"] = ms[date_col].dt.year
        ms = ms.rename(columns={mid_col: "match_id"})
    else:
        ms = pd.DataFrame(columns=["match_id", "season"])

    # ─────────────────────────────────────────────────────────────────────────
    # BATTING MODE
    # ─────────────────────────────────────────────────────────────────────────
    if mode == "batting":
        bat = batting.copy()

        # Resolve player name
        bat_id_col = _col(bat, "batsman_id", "batsman_name")
        if bat_id_col and player_name:
            if bat_id_col == "batsman_id" and "player_id" in players.columns:
                id_map = players.set_index("player_id")["player_name"].to_dict()
                bat["_pname"] = bat[bat_id_col].map(id_map).fillna(bat[bat_id_col].astype(str))
            else:
                bat["_pname"] = bat[bat_id_col].astype(str)
            bat = bat[bat["_pname"].str.strip() == player_name.strip()]

        # Team filter
        if team and "team" in bat.columns:
            bat = bat[bat["team"] == team]

        if bat.empty:
            return pd.DataFrame(), []

        # Numeric cols
        for c in ["runs", "balls", "sixes", "fours"]:
            if c in bat.columns:
                bat[c] = pd.to_numeric(bat[c], errors="coerce").fillna(0)

        # ── Fig 1: Runs by batting position bucket × phase ────────────────────
        # We'll use (innings position approximation from wickets col if available)
        # Phase buckets: PP=1-6, Middle=7-15, Death=16-20
        # Since we have match-level data (not ball-level), use over approximation
        # via 'balls' faced: 1-36 = PP, 37-90 = middle, 91+ = death

        phase_data = []

        if "balls" in bat.columns and "runs" in bat.columns:
            bat["phase"] = pd.cut(
                bat["balls"].cumsum() if "balls" in bat.columns else bat["balls"],
                bins=[0, 36, 90, 9999],
                labels=["Powerplay (1-6)", "Middle (7-15)", "Death (16-20)"],
            )
            # Fallback: distribute evenly
            bat = bat.reset_index(drop=True)
            n = len(bat)
            bat["phase"] = pd.Categorical(
                ["Powerplay (1-6)"] * (n // 3)
                + ["Middle (7-15)"] * (n // 3)
                + ["Death (16-20)"] * (n - 2 * (n // 3)),
                categories=["Powerplay (1-6)", "Middle (7-15)", "Death (16-20)"],
            )

        # Group by phase
        if "phase" in bat.columns:
            grp = bat.groupby("phase", observed=True).agg(
                total_runs=("runs", "sum"),
                total_balls=("balls", "sum") if "balls" in bat.columns else ("runs", "count"),
                sixes=("sixes", "sum") if "sixes" in bat.columns else ("runs", "count"),
                fours=("fours", "sum") if "fours" in bat.columns else ("runs", "count"),
            ).reset_index()
            grp["sr"] = (grp["total_runs"] / grp["total_balls"].replace(0, np.nan) * 100).round(1)

            fig1 = go.Figure()
            colors = ["#378ADD", "#EF9F27", "#D85A30"]
            for i, row in grp.iterrows():
                fig1.add_trace(go.Bar(
                    x=[row["phase"]],
                    y=[row["total_runs"]],
                    name=str(row["phase"]),
                    marker_color=colors[i % 3],
                    text=f"{int(row['total_runs'])} runs<br>SR: {row['sr']}",
                    textposition="outside",
                    hovertemplate=(
                        f"<b>{row['phase']}</b><br>"
                        f"Runs: {int(row['total_runs'])}<br>"
                        f"SR: {row['sr']}<br>"
                        f"6s: {int(row.get('sixes', 0))}  4s: {int(row.get('fours', 0))}"
                        "<extra></extra>"
                    ),
                ))
            title_str = f"Scoring Zones — {player_name}" if player_name else "Scoring Zones by Phase"
            fig1.update_layout(
                title=dict(text=title_str, x=0.5, font=dict(size=15)),
                xaxis_title="Match Phase",
                yaxis_title="Total Runs",
                plot_bgcolor="#161b22", paper_bgcolor="#0d1117",
                font_color="#e6edf3",
                showlegend=False,
                margin=dict(l=40, r=40, t=60, b=40),
                height=380,
            )
            figs.append(fig1)

        # ── Fig 2: Runs heatmap — season × phase (if season available) ────────
        if not ms.empty and "match_id" in bat.columns:
            bat2 = bat.merge(ms[["match_id", "season"]], on="match_id", how="left")
            if "season" in bat2.columns and "phase" in bat2.columns:
                pivot = bat2.groupby(["season", "phase"], observed=True)["runs"].sum().unstack(fill_value=0)
                pivot.columns = [str(c) for c in pivot.columns]

                fig2 = go.Figure(go.Heatmap(
                    z=pivot.values,
                    x=list(pivot.columns),
                    y=[str(s) for s in pivot.index],
                    colorscale="YlOrRd",
                    text=pivot.values,
                    texttemplate="%{text}",
                    hovertemplate="Season: %{y}<br>Phase: %{x}<br>Runs: %{z}<extra></extra>",
                    colorbar=dict(title="Runs"),
                ))
                fig2.update_layout(
                    title=dict(text="Runs Heatmap — Season × Phase", x=0.5),
                    xaxis_title="Phase",
                    yaxis_title="Season",
                    plot_bgcolor="#161b22", paper_bgcolor="#0d1117",
                    font_color="#e6edf3",
                    margin=dict(l=60, r=40, t=60, b=40),
                    height=420,
                )
                figs.append(fig2)

        return grp if "grp" in dir() else pd.DataFrame(), figs

    # ─────────────────────────────────────────────────────────────────────────
    # BOWLING MODE
    # ─────────────────────────────────────────────────────────────────────────
    else:
        bowl = bowling.copy()

        # Resolve player
        bowl_id_col = _col(bowl, "bowler_id", "bowler_name")
        if bowl_id_col and player_name:
            if bowl_id_col == "bowler_id" and "player_id" in players.columns:
                id_map = players.set_index("player_id")["player_name"].to_dict()
                bowl["_pname"] = bowl[bowl_id_col].map(id_map).fillna(bowl[bowl_id_col].astype(str))
            else:
                bowl["_pname"] = bowl[bowl_id_col].astype(str)
            bowl = bowl[bowl["_pname"].str.strip() == player_name.strip()]

        if team and "team" in bowl.columns:
            bowl = bowl[bowl["team"] == team]

        if bowl.empty:
            return pd.DataFrame(), []

        for c in ["wickets", "conceded", "runs_conceded", "overs", "economy", "dots"]:
            if c in bowl.columns:
                bowl[c] = pd.to_numeric(bowl[c], errors="coerce").fillna(0)

        runs_col = _col(bowl, "conceded", "runs_conceded")

        # ── Fig 1: Economy by over bucket (PP / Middle / Death) ───────────────
        if "overs" in bowl.columns and runs_col:
            bowl["phase"] = pd.cut(
                bowl["overs"],
                bins=[0, 6, 15, 20],
                labels=["Powerplay", "Middle overs", "Death overs"],
            )
            grp = bowl.groupby("phase", observed=True).agg(
                runs=(runs_col, "sum"),
                overs=("overs", "sum"),
                wickets=("wickets", "sum") if "wickets" in bowl.columns else (runs_col, "count"),
                dots=("dots", "sum") if "dots" in bowl.columns else (runs_col, "count"),
            ).reset_index()
            grp["economy"] = (grp["runs"] / grp["overs"].replace(0, np.nan)).round(2)
            grp["dot_pct"] = (grp["dots"] / (grp["overs"] * 6).replace(0, np.nan) * 100).round(1)

            colors_bowl = ["#1D9E75", "#EF9F27", "#D85A30"]
            fig3 = go.Figure()
            for i, row in grp.iterrows():
                fig3.add_trace(go.Bar(
                    x=[str(row["phase"])],
                    y=[row["economy"]],
                    name=str(row["phase"]),
                    marker_color=colors_bowl[i % 3],
                    text=f"Econ: {row['economy']}<br>Wkts: {int(row['wickets'])}",
                    textposition="outside",
                ))
            title_str = f"Bowling Zones — {player_name}" if player_name else "Economy by Phase"
            fig3.update_layout(
                title=dict(text=title_str, x=0.5, font=dict(size=15)),
                xaxis_title="Phase",
                yaxis_title="Economy Rate",
                plot_bgcolor="#161b22", paper_bgcolor="#0d1117",
                font_color="#e6edf3",
                showlegend=False,
                margin=dict(l=40, r=40, t=60, b=40),
                height=380,
            )
            figs.append(fig3)

        # ── Fig 2: Wickets + Economy scatter by opposition team ───────────────
        opp_col = _col(bowl, "opposition", "opponent", "batting_team")
        if opp_col and runs_col:
            opp_grp = bowl.groupby(opp_col).agg(
                wickets=("wickets", "sum") if "wickets" in bowl.columns else (runs_col, "count"),
                overs=("overs", "sum") if "overs" in bowl.columns else (runs_col, "count"),
                runs=(runs_col, "sum"),
            ).reset_index()
            opp_grp["economy"] = (opp_grp["runs"] / opp_grp["overs"].replace(0, np.nan)).round(2)
            opp_grp = opp_grp.sort_values("wickets", ascending=False).head(15)

            fig4 = px.scatter(
                opp_grp, x="economy", y="wickets",
                text=opp_col,
                color="wickets", color_continuous_scale="Reds",
                size="overs",
                labels={"economy": "Economy Rate", "wickets": "Wickets"},
                title=f"Performance vs Opposition — {player_name}" if player_name else "Performance vs Opposition",
            )
            fig4.update_traces(textposition="top center")
            fig4.update_layout(
                plot_bgcolor="#161b22", paper_bgcolor="#0d1117",
                font_color="#e6edf3",
                margin=dict(l=40, r=40, t=60, b=40),
                height=420,
            )
            figs.append(fig4)

        return grp if "grp" in dir() else pd.DataFrame(), figs


# ══════════════════════════════════════════════════════════════════════════════
# B. BATSMAN–BOWLER INTERACTION MATRIX
#    Returns a pivot heatmap: rows = batsmen, cols = bowlers
#    Cell value = scoring probability OR dismissal probability
# ══════════════════════════════════════════════════════════════════════════════

def analysis_batsman_bowler_matrix(
    batting:  pd.DataFrame,
    bowling:  pd.DataFrame,
    players:  pd.DataFrame,
    metric: str = "runs",          # "runs" | "dismissal_pct" | "sr"
    top_n_bat: int = 10,
    top_n_bowl: int = 10,
) -> tuple[pd.DataFrame, go.Figure]:
    """
    Batsman–Bowler Interaction Matrix.

    Joins batting + bowling on match_id + innings to build a pivot table.
    Each cell shows: total runs / dismissal % / strike rate for that pair.

    Returns
    -------
    pivot_df : pivot table (batsmen × bowlers)
    fig      : Plotly heatmap figure
    """

    # ── Column detection ──────────────────────────────────────────────────────
    def _col(df, *names):
        return next((c for c in names if c in df.columns), None)

    bat_id  = _col(batting,  "batsman_id",  "batsman_name")
    bowl_id = _col(bowling,  "bowler_id",   "bowler_name")
    mid_bat = _col(batting,  "match_id",    "Match ID")
    mid_bow = _col(bowling,  "match_id",    "Match ID")

    if not all([bat_id, bowl_id, mid_bat, mid_bow]):
        return pd.DataFrame(), go.Figure()

    # ── Resolve player names ──────────────────────────────────────────────────
    id_map = {}
    if "player_id" in players.columns and "player_name" in players.columns:
        id_map = players.set_index("player_id")["player_name"].to_dict()

    def _resolve(df, id_col, name):
        df = df.copy()
        if id_col.endswith("_id") and id_map:
            df[name] = df[id_col].map(id_map).fillna(df[id_col].astype(str))
        else:
            df[name] = df[id_col].astype(str)
        return df

    bat  = _resolve(batting,  bat_id,  "_bat_name")
    bowl = _resolve(bowling,  bowl_id, "_bowl_name")

    # ── Top batsmen & bowlers by volume ───────────────────────────────────────
    top_bats  = (
        bat.groupby("_bat_name")["runs"].sum()
        .nlargest(top_n_bat).index.tolist()
        if "runs" in bat.columns else bat["_bat_name"].value_counts().head(top_n_bat).index.tolist()
    )
    top_bowls = (
        bowl.groupby("_bowl_name")["wickets"].sum()
        .nlargest(top_n_bowl).index.tolist()
        if "wickets" in bowl.columns else bowl["_bowl_name"].value_counts().head(top_n_bowl).index.tolist()
    )

    bat  = bat[bat["_bat_name"].isin(top_bats)]
    bowl = bowl[bowl["_bowl_name"].isin(top_bowls)]

    # ── Build interaction via match_id + innings ───────────────────────────────
    inn_bat  = _col(bat,  "innings")
    inn_bowl = _col(bowl, "innings")

    bat  = bat.rename(columns={mid_bat: "_mid"})
    bowl = bowl.rename(columns={mid_bow: "_mid"})

    merge_keys = ["_mid"]
    if inn_bat and inn_bowl:
        bat  = bat.rename(columns={inn_bat:  "_inn"})
        bowl = bowl.rename(columns={inn_bowl: "_inn"})
        merge_keys.append("_inn")

    # Select minimal columns
    bat_cols  = ["_bat_name",  "_mid"] + (["_inn"] if "_inn" in bat.columns  else []) + [c for c in ["runs","balls","isOut","wicketType"] if c in bat.columns]
    bowl_cols = ["_bowl_name", "_mid"] + (["_inn"] if "_inn" in bowl.columns else []) + [c for c in ["wickets","conceded","runs_conceded","overs","economy"] if c in bowl.columns]

    merged = bat[bat_cols].merge(
        bowl[bowl_cols],
        on=merge_keys,
        how="inner",
    )

    if merged.empty:
        return pd.DataFrame(), go.Figure()

    # ── Compute metric ─────────────────────────────────────────────────────────
    if metric == "runs" and "runs" in merged.columns:
        pivot = merged.groupby(["_bat_name", "_bowl_name"])["runs"].sum().unstack(fill_value=0)
        colorscale = "YlOrRd"
        title_metric = "Total Runs Scored"
        fmt = ".0f"

    elif metric == "dismissal_pct" and "isOut" in merged.columns:
        merged["_is_out"] = merged["isOut"].map(
            lambda x: 1 if str(x).upper() in ("TRUE", "1", "YES") else 0
        )
        grp = merged.groupby(["_bat_name", "_bowl_name"]).agg(
            dismissals=("_is_out", "sum"),
            balls=("balls", "sum") if "balls" in merged.columns else ("_is_out", "count"),
        )
        grp["dismissal_pct"] = (grp["dismissals"] / grp["balls"].replace(0, np.nan) * 100).round(1)
        pivot = grp["dismissal_pct"].unstack(fill_value=0)
        colorscale = "Reds"
        title_metric = "Dismissal Probability (%)"
        fmt = ".1f"

    elif metric == "sr" and "runs" in merged.columns and "balls" in merged.columns:
        grp = merged.groupby(["_bat_name", "_bowl_name"]).agg(
            runs=("runs", "sum"),
            balls=("balls", "sum"),
        )
        grp["sr"] = (grp["runs"] / grp["balls"].replace(0, np.nan) * 100).round(1)
        pivot = grp["sr"].unstack(fill_value=0)
        colorscale = "RdYlGn"
        title_metric = "Strike Rate"
        fmt = ".1f"

    else:
        # fallback to runs count
        pivot = merged.groupby(["_bat_name", "_bowl_name"]).size().unstack(fill_value=0)
        colorscale = "Blues"
        title_metric = "Encounters"
        fmt = ".0f"

    # ── Plot ──────────────────────────────────────────────────────────────────
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[str(c) for c in pivot.columns],
        y=[str(r) for r in pivot.index],
        colorscale=colorscale,
        text=np.round(pivot.values, 1),
        texttemplate=f"%{{text:{fmt}}}",
        hovertemplate="Batsman: %{y}<br>Bowler: %{x}<br>" + title_metric + ": %{z}<extra></extra>",
        colorbar=dict(title=title_metric, thickness=12),
    ))

    fig.update_layout(
        title=dict(
            text=f"Batsman–Bowler Interaction Matrix — {title_metric}",
            x=0.5, font=dict(size=15),
        ),
        xaxis=dict(title="Bowler", tickangle=-40, side="bottom"),
        yaxis=dict(title="Batsman", autorange="reversed"),
        plot_bgcolor="#161b22", paper_bgcolor="#0d1117",
        font_color="#e6edf3",
        margin=dict(l=160, r=40, t=70, b=140),
        height=max(400, top_n_bat * 42 + 180),
    )

    return pivot, fig


# ══════════════════════════════════════════════════════════════════════════════
# C. SEASONAL TRENDS DASHBOARD
#    Moving averages + anomaly detection (Z-score based)
#    Works for team OR player, batting OR bowling
# ══════════════════════════════════════════════════════════════════════════════

def analysis_seasonal_trends(
    batting:  pd.DataFrame,
    bowling:  pd.DataFrame,
    players:  pd.DataFrame,
    matches:  pd.DataFrame,
    entity_type: str = "player",     # "player" | "team"
    entity_name: str = None,         # player name or team name
    metric: str = "runs",            # "runs" | "sr" | "wickets" | "economy"
    window: int = 3,                 # moving average window (seasons)
) -> tuple[pd.DataFrame, list]:
    """
    Seasonal Trends Dashboard.

    Features:
    - Season-by-season metric line
    - Rolling moving average (window seasons)
    - Anomaly bands (±1.5σ from moving mean)
    - Annotated anomaly points (spike/slump)

    Returns
    -------
    trend_df : DataFrame with season metrics + MA + anomaly flags
    figs     : list of Plotly figures
    """

    def _col(df, *names):
        return next((c for c in names if c in df.columns), None)

    figs = []

    # ── Attach season ──────────────────────────────────────────────────────────
    mid_col  = _col(matches, "Match ID", "match_id")
    date_col = _col(matches, "Match Date", "date", "match_date")

    if mid_col and date_col:
        ms = matches[[mid_col, date_col]].copy()
        ms[date_col] = pd.to_datetime(ms[date_col], errors="coerce")
        ms["season"] = ms[date_col].dt.year
        ms = ms.rename(columns={mid_col: "match_id"})
    else:
        return pd.DataFrame(), []

    # ── Select source dataframe ────────────────────────────────────────────────
    is_batting = metric in ("runs", "sr", "fours", "sixes")
    src = batting.copy() if is_batting else bowling.copy()

    # ── Resolve entity ─────────────────────────────────────────────────────────
    if entity_type == "player":
        id_col = _col(src,
                      "batsman_id" if is_batting else "bowler_id",
                      "batsman_name" if is_batting else "bowler_name")
        if id_col and entity_name:
            if id_col.endswith("_id") and "player_id" in players.columns:
                id_map = players.set_index("player_id")["player_name"].to_dict()
                src["_ename"] = src[id_col].map(id_map).fillna(src[id_col].astype(str))
            else:
                src["_ename"] = src[id_col].astype(str)
            src = src[src["_ename"].str.strip() == entity_name.strip()]
    else:  # team
        team_col = _col(src, "team", "batting_team", "bowling_team")
        if team_col and entity_name:
            src = src[src[team_col] == entity_name]

    if src.empty:
        return pd.DataFrame(), []

    # ── Attach season ──────────────────────────────────────────────────────────
    mid_src = _col(src, "match_id", "Match ID")
    if mid_src:
        src = src.rename(columns={mid_src: "match_id"}) if mid_src != "match_id" else src
        src = src.merge(ms[["match_id", "season"]], on="match_id", how="left")
    else:
        return pd.DataFrame(), []

    if "season" not in src.columns or src["season"].isna().all():
        return pd.DataFrame(), []

    # ── Aggregate per season ───────────────────────────────────────────────────
    for c in ["runs", "balls", "wickets", "conceded", "runs_conceded", "overs",
              "sixes", "fours", "economy"]:
        if c in src.columns:
            src[c] = pd.to_numeric(src[c], errors="coerce").fillna(0)

    if metric == "runs" and "runs" in src.columns:
        agg = src.groupby("season")["runs"].sum().reset_index(name="value")
        ylabel = "Runs"
    elif metric == "sr" and "runs" in src.columns and "balls" in src.columns:
        g = src.groupby("season").agg(runs=("runs","sum"), balls=("balls","sum")).reset_index()
        g["value"] = (g["runs"] / g["balls"].replace(0, np.nan) * 100).round(1)
        agg = g[["season","value"]]
        ylabel = "Strike Rate"
    elif metric == "wickets" and "wickets" in src.columns:
        agg = src.groupby("season")["wickets"].sum().reset_index(name="value")
        ylabel = "Wickets"
    elif metric == "economy":
        runs_c = _col(src, "conceded", "runs_conceded")
        overs_c = _col(src, "overs")
        if runs_c and overs_c:
            g = src.groupby("season").agg(runs=(runs_c,"sum"), overs=(overs_c,"sum")).reset_index()
            g["value"] = (g["runs"] / g["overs"].replace(0, np.nan)).round(2)
            agg = g[["season","value"]]
        else:
            return pd.DataFrame(), []
        ylabel = "Economy Rate"
    elif metric == "sixes" and "sixes" in src.columns:
        agg = src.groupby("season")["sixes"].sum().reset_index(name="value")
        ylabel = "Sixes"
    elif metric == "fours" and "fours" in src.columns:
        agg = src.groupby("season")["fours"].sum().reset_index(name="value")
        ylabel = "Fours"
    else:
        return pd.DataFrame(), []

    agg = agg.sort_values("season").reset_index(drop=True)
    agg["value"] = pd.to_numeric(agg["value"], errors="coerce")

    # ── Moving average ─────────────────────────────────────────────────────────
    agg["ma"] = agg["value"].rolling(window=window, min_periods=1, center=True).mean().round(2)

    # ── Anomaly detection (Z-score) ───────────────────────────────────────────
    mu = agg["value"].mean()
    sigma = agg["value"].std()
    
    sigma = np.nan if sigma == 0 else sigma
    
    agg["z_score"] = ((agg["value"] - mu) / sigma).round(2)
    agg["anomaly"] = agg["z_score"].abs() > 1.5
    agg["anomaly_type"] = np.where(
        agg["z_score"] >  1.5, "spike",
        np.where(agg["z_score"] < -1.5, "slump", "normal")
    )

    # Upper / lower bands (MA ± 1.5σ rolling)
    agg["upper"] = (agg["ma"] + 1.5 * sigma).round(2)
    agg["lower"] = (agg["ma"] - 1.5 * sigma).round(2)

    # ── Build figure ───────────────────────────────────────────────────────────
    fig = go.Figure()

    # Anomaly band (fill)
    fig.add_trace(go.Scatter(
        x=pd.concat([agg["season"], agg["season"][::-1]]),
        y=pd.concat([agg["upper"], agg["lower"][::-1]]),
        fill="toself",
        fillcolor="rgba(55,138,221,0.08)",
        line=dict(color="rgba(0,0,0,0)"),
        showlegend=True,
        name="Normal band (±1.5σ)",
        hoverinfo="skip",
    ))

    # Moving average line
    fig.add_trace(go.Scatter(
        x=agg["season"], y=agg["ma"],
        mode="lines",
        line=dict(color="#EF9F27", width=2, dash="dash"),
        name=f"{window}-season MA",
        hovertemplate="Season: %{x}<br>MA: %{y}<extra></extra>",
    ))

    # Actual value line
    fig.add_trace(go.Scatter(
        x=agg["season"], y=agg["value"],
        mode="lines+markers",
        line=dict(color="#378ADD", width=2),
        marker=dict(
            color=np.where(agg["anomaly_type"] == "spike", "#D85A30",
                   np.where(agg["anomaly_type"] == "slump", "#9B59B6", "#378ADD")),
            size=np.where(agg["anomaly"], 12, 7),
            line=dict(width=1.5, color="#0d1117"),
        ),
        name=ylabel,
        customdata=np.stack([agg["z_score"], agg["anomaly_type"]], axis=1),
        hovertemplate=(
            "Season: %{x}<br>"
            f"{ylabel}: %{{y}}<br>"
            "Z-score: %{customdata[0]}<br>"
            "Status: %{customdata[1]}"
            "<extra></extra>"
        ),
    ))

    # Annotate anomalies
    for _, row in agg[agg["anomaly"]].iterrows():
        color = "#D85A30" if row["anomaly_type"] == "spike" else "#9B59B6"
        label = f"▲ {row['anomaly_type'].capitalize()}" if row["anomaly_type"] == "spike" else f"▼ {row['anomaly_type'].capitalize()}"
        fig.add_annotation(
            x=row["season"], y=row["value"],
            text=label,
            showarrow=True, arrowhead=2, arrowcolor=color,
            font=dict(color=color, size=10),
            bgcolor="#0d1117", bordercolor=color, borderwidth=1,
            ay=-30 if row["anomaly_type"] == "spike" else 30, ax=0,
        )

    entity_label = entity_name or "All"
    fig.update_layout(
        title=dict(
            text=f"Seasonal Trend — {entity_label} — {ylabel}",
            x=0.5, font=dict(size=15),
        ),
        xaxis=dict(
            title="Season", dtick=1, tickangle=-45,
            gridcolor="#21262d", linecolor="#30363d",
        ),
        yaxis=dict(
            title=ylabel,
            gridcolor="#21262d", linecolor="#30363d",
        ),
        plot_bgcolor="#161b22", paper_bgcolor="#0d1117",
        font_color="#e6edf3",
        legend=dict(orientation="h", y=1.08, x=0),
        margin=dict(l=50, r=40, t=70, b=70),
        height=460,
    )
    figs.append(fig)

    # ── Fig 2: Anomaly summary bar ─────────────────────────────────────────────
    fig2 = go.Figure()
    bar_colors = [
        "#D85A30" if a == "spike" else "#9B59B6" if a == "slump" else "#378ADD"
        for a in agg["anomaly_type"]
    ]
    fig2.add_trace(go.Bar(
        x=agg["season"],
        y=agg["z_score"],
        marker_color=bar_colors,
        text=agg["z_score"].round(2),
        textposition="outside",
        hovertemplate="Season: %{x}<br>Z-score: %{y}<extra></extra>",
    ))
    fig2.add_hline(y=1.5,  line_dash="dash", line_color="#D85A30", line_width=1,
                   annotation_text="+1.5σ spike", annotation_font_color="#D85A30")
    fig2.add_hline(y=-1.5, line_dash="dash", line_color="#9B59B6", line_width=1,
                   annotation_text="-1.5σ slump", annotation_font_color="#9B59B6")
    fig2.add_hline(y=0,    line_dash="solid", line_color="#888780", line_width=0.5)

    fig2.update_layout(
        title=dict(text="Anomaly Score (Z-score) per Season", x=0.5, font=dict(size=14)),
        xaxis=dict(dtick=1, tickangle=-45, gridcolor="#21262d"),
        yaxis=dict(title="Z-score", gridcolor="#21262d"),
        plot_bgcolor="#161b22", paper_bgcolor="#0d1117",
        font_color="#e6edf3",
        showlegend=False,
        margin=dict(l=50, r=40, t=50, b=70),
        height=300,
    )
    figs.append(fig2)

    return agg, figs