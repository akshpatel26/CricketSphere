"""
odi_analysis.py  —  fixed version
All functions accept both  players=  and  players_df=  keyword forms.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _resolve_players(players, players_df):
    """Accept either keyword form."""
    if players_df is not None:
        return players_df
    return players


# ══════════════════════════════════════════════════════════════════════════════
# 1. Host countries
# ══════════════════════════════════════════════════════════════════════════════
def analysis_host_countries(matches: pd.DataFrame,
                             top_n: int = 15) -> tuple:
    for col in ('Match Venue (Country)', 'Match Venue (City)',
                'Match Venue (Stadium)', 'venue', 'Venue', 'country'):
        if col in matches.columns:
            host_col = col
            break
    else:
        return pd.DataFrame(), go.Figure()

    df = (
        matches[host_col]
        .dropna()
        .value_counts()
        .reset_index()
        .head(top_n)
    )
    df.columns = ['country', 'matches_hosted']

    fig = px.bar(
        df, x='matches_hosted', y='country', orientation='h',
        color='matches_hosted', color_continuous_scale='Viridis',
        text='matches_hosted',
    )
    fig.update_traces(textposition='inside', textfont=dict(color='white', size=12))
    fig.update_layout(
        title={'text': '🌍 Countries That Hosted Most ODI Matches', 'x': 0.5, 'xanchor': 'center'},
        xaxis_title='Matches Hosted', yaxis_title='Country',
        yaxis={'categoryorder': 'total ascending'},
        coloraxis_showscale=False, template='plotly_dark', height=550,
    )
    return df, fig

# ══════════════════════════════════════════════════════════════════════════════
# Venue Analysis — ODI
# ══════════════════════════════════════════════════════════════════════════════

def analysis_venue(matches: pd.DataFrame,
                   selected_venue: str = None) -> tuple[pd.DataFrame, dict, list]:

    # ── Column mapping ────────────────────────────────────────────
    stadium_col = next((c for c in ("Match Venue (Stadium)", "venue", "stadium")     if c in matches.columns), None)
    city_col    = next((c for c in ("Match Venue (City)",    "city")                 if c in matches.columns), None)
    country_col = next((c for c in ("Match Venue (Country)", "country")              if c in matches.columns), None)
    t1_runs_col = next((c for c in ("Team1 Runs Scored",     "team1_runs")           if c in matches.columns), None)
    t2_runs_col = next((c for c in ("Team2 Runs Scored",     "team2_runs")           if c in matches.columns), None)
    toss_col    = next((c for c in ("Toss Winner",           "toss_winner")          if c in matches.columns), None)
    winner_col  = next((c for c in ("Match Winner",          "winner")               if c in matches.columns), None)
    t2_col      = next((c for c in ("Team2 Name",            "team2")                if c in matches.columns), None)
    mid_col     = next((c for c in ("Match ID",              "match_id")             if c in matches.columns), None)

    if not stadium_col or not t1_runs_col or not t2_runs_col:
        return pd.DataFrame(), {}, []

    df = matches.copy()
    df[t1_runs_col] = pd.to_numeric(df[t1_runs_col], errors="coerce")
    df[t2_runs_col] = pd.to_numeric(df[t2_runs_col], errors="coerce")

    # Chasing win: team2 (batting 2nd) won
    if winner_col and t2_col:
        df["chase_win"] = (df[winner_col] == df[t2_col]).astype(int)
    else:
        df["chase_win"] = np.nan

    # Toss impact: toss winner = match winner
    if toss_col and winner_col:
        df["toss_win_match"] = (df[toss_col] == df[winner_col]).astype(int)
    else:
        df["toss_win_match"] = np.nan

    # ── Aggregate per venue ───────────────────────────────────────
    agg = {
        "matches": (mid_col or t1_runs_col, "count"),
        "avg_1st": (t1_runs_col, "mean"),
        "avg_2nd": (t2_runs_col, "mean"),
        "highest": (t1_runs_col, "max"),
        "lowest":  (t1_runs_col, "min"),
    }
    if "chase_win"      in df.columns: agg["chase_wins"] = ("chase_win",      "sum")
    if "toss_win_match" in df.columns: agg["toss_wins"]  = ("toss_win_match", "sum")

    venue_df = (
        df.groupby(stadium_col)
        .agg(**agg)
        .reset_index()
        .rename(columns={stadium_col: "venue"})
    )

    venue_df["avg_1st"] = venue_df["avg_1st"].round(1)
    venue_df["avg_2nd"] = venue_df["avg_2nd"].round(1)
    venue_df["highest"] = venue_df["highest"].astype(int)
    venue_df["lowest"]  = venue_df["lowest"].astype(int)

    if "chase_wins" in venue_df.columns:
        venue_df["chase_win_pct"] = (
            venue_df["chase_wins"] / venue_df["matches"] * 100
        ).round(1)

    if "toss_wins" in venue_df.columns:
        venue_df["toss_impact_pct"] = (
            venue_df["toss_wins"] / venue_df["matches"] * 100
        ).round(1)

    venue_df = venue_df.sort_values("matches", ascending=False).reset_index(drop=True)

    # City / Country map
    if city_col:
        venue_df["city"]    = venue_df["venue"].map(df.groupby(stadium_col)[city_col].first())
    if country_col:
        venue_df["country"] = venue_df["venue"].map(df.groupby(stadium_col)[country_col].first())

    # ── Selected venue stats ──────────────────────────────────────
    venue_stats = {}
    if selected_venue and selected_venue in venue_df["venue"].values:
        row = venue_df[venue_df["venue"] == selected_venue].iloc[0]
        venue_stats = {
            "matches":         int(row["matches"]),
            "highest":         int(row["highest"]),
            "lowest":          int(row["lowest"]),
            "avg_1st":         float(row["avg_1st"]),
            "avg_2nd":         float(row["avg_2nd"]),
            "chase_win_pct":   float(row.get("chase_win_pct",   0)),
            "toss_impact_pct": float(row.get("toss_impact_pct", 0)),
        }

    # ── Figures ───────────────────────────────────────────────────
    figs = []
    top15 = venue_df.head(15)

    # Fig 1: Avg 1st vs 2nd innings grouped bar
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(
        name="Avg 1st Innings", x=top15["venue"], y=top15["avg_1st"],
        marker_color="#378ADD", text=top15["avg_1st"], textposition="outside",
    ))
    fig1.add_trace(go.Bar(
        name="Avg 2nd Innings", x=top15["venue"], y=top15["avg_2nd"],
        marker_color="#D85A30", text=top15["avg_2nd"], textposition="outside",
    ))
    fig1.update_layout(
        barmode="group",
        title={"text": "Avg 1st vs 2nd Innings Score by Venue", "x": 0.5},
        xaxis_tickangle=-45,
        plot_bgcolor="#161b22", paper_bgcolor="#0d1117", font_color="#e6edf3",
        legend=dict(orientation="h", y=1.1),
        margin=dict(l=20, r=20, t=60, b=120),
        height=520,
    )
    figs.append(fig1)

    # Fig 2: Chasing Win % — horizontal bar + color zones
    if "chase_win_pct" in top15.columns:
        chase_df = top15.sort_values("chase_win_pct", ascending=True)
        colors   = ["#1D9E75" if v >= 55 else "#D85A30" if v <= 45 else "#EF9F27"
                    for v in chase_df["chase_win_pct"]]

        fig2 = go.Figure(go.Bar(
            x=chase_df["chase_win_pct"], y=chase_df["venue"],
            orientation="h", marker_color=colors,
            text=[f"{v}%" for v in chase_df["chase_win_pct"]],
            textposition="outside",
        ))
        fig2.add_vline(x=50, line_dash="dash", line_color="#888780", line_width=1.5,
                       annotation_text="50% mark", annotation_position="top",
                       annotation_font_color="#888780")
        fig2.update_layout(
            title={"text": "🏃 Chasing Win % by Venue", "x": 0.5},
            xaxis=dict(title="Chasing Win %", range=[0, 80]),
            plot_bgcolor="#161b22", paper_bgcolor="#0d1117", font_color="#e6edf3",
            margin=dict(l=20, r=60, t=50, b=20), height=520, showlegend=False,
        )
        figs.append(fig2)

    # Fig 3: Toss Impact — Lollipop chart
    if "toss_impact_pct" in top15.columns:
        toss_df = top15.sort_values("toss_impact_pct", ascending=True)

        fig3 = go.Figure()
        for _, row in toss_df.iterrows():
            fig3.add_shape(
                type="line",
                x0=50, x1=row["toss_impact_pct"],
                y0=row["venue"], y1=row["venue"],
                line=dict(
                    color="#1D9E75" if row["toss_impact_pct"] >= 50 else "#D85A30",
                    width=2,
                ),
            )
        fig3.add_trace(go.Scatter(
            x=toss_df["toss_impact_pct"], y=toss_df["venue"],
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
        fig3.add_vline(x=50, line_dash="dash", line_color="#888780", line_width=1.5,
                       annotation_text="50% (random chance)", annotation_position="top",
                       annotation_font_color="#888780")
        fig3.update_layout(
            title={"text": "🪙 Toss Impact % by Venue", "x": 0.5},
            xaxis=dict(title="Toss Winner = Match Winner %", range=[25, 75]),
            plot_bgcolor="#161b22", paper_bgcolor="#0d1117", font_color="#e6edf3",
            margin=dict(l=20, r=80, t=50, b=20), height=520, showlegend=False,
        )
        figs.append(fig3)

    return venue_df, venue_stats, figs
# ══════════════════════════════════════════════════════════════════════════════
# 3. Highest wicket-takers in ODI Internationals
# ══════════════════════════════════════════════════════════════════════════════
def analysis_wicket_takers(bowling: pd.DataFrame,
                            players=None,
                            top_n: int = 10,
                            players_df=None) -> tuple:
    players = _resolve_players(players, players_df)

    if bowling.empty:
        return pd.DataFrame(), go.Figure()

    # Column detect karo
    name_col = None
    for c in ("bowler_name", "bowler_id", "bowler id"):
        if c in bowling.columns:
            name_col = c
            break
    if name_col is None:
        return pd.DataFrame(), go.Figure()

    # ID hoy to name map karo
    if (name_col in ("bowler_id", "bowler id")
            and players is not None
            and not players.empty
            and "player_id" in players.columns
            and "player_name" in players.columns):
        id_map = players.set_index("player_id")["player_name"].to_dict()
        bowling = bowling.copy()
        bowling["bowler_display"] = (
            bowling[name_col].map(id_map).fillna(bowling[name_col].astype(str))
        )
        name_col = "bowler_display"

    # Aggregate — jo jo column hoy te j use karo
    agg_cols = {}
    if "wickets"       in bowling.columns: agg_cols["wickets"]       = ("wickets",       "sum")
    if "Match ID"      in bowling.columns: agg_cols["matches"]       = ("Match ID",      "nunique")
    elif "match_id"    in bowling.columns: agg_cols["matches"]       = ("match_id",      "nunique")
    if "runs_conceded" in bowling.columns: agg_cols["runs_conceded"] = ("runs_conceded", "sum")
    if "overs"         in bowling.columns: agg_cols["overs"]         = ("overs",         "sum")
    if "economy"       in bowling.columns: agg_cols["avg_economy"]   = ("economy",       "mean")

    df = (
        bowling.groupby(name_col)
        .agg(**agg_cols)
        .reset_index()
        .rename(columns={name_col: "player"})
    )

    # Economy calculate karo jો direct na mili hoy
    if "avg_economy" in df.columns:
        df["avg_economy"] = df["avg_economy"].round(2)
    elif "runs_conceded" in df.columns and "overs" in df.columns:
        df["avg_economy"] = (
            df["runs_conceded"] / df["overs"].replace(0, pd.NA)
        ).round(2)

    df = df.sort_values("wickets", ascending=False).head(top_n).reset_index(drop=True)

    fig = px.bar(
        df, x="wickets", y="player", orientation="h",
        color="avg_economy" if "avg_economy" in df.columns else "wickets",
        color_continuous_scale="RdYlGn_r",
        labels={"wickets": "Wickets", "player": "Bowler", "avg_economy": "Economy"},
        text="wickets",
        hover_data=[c for c in ["matches", "avg_economy", "runs_conceded"] if c in df.columns],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        yaxis=dict(autorange="reversed"),
        template="plotly_dark",
        height=550,
        title={"text": "🎯 Highest Wicket-Takers in ODI Internationals",
               "x": 0.5, "xanchor": "center"},
    )
    return df, fig


# ══════════════════════════════════════════════════════════════════════════════
# 4. Run scorers
# ══════════════════════════════════════════════════════════════════════════════
def analysis_run_scorers(batting: pd.DataFrame,
                          players=None,
                          top_n: int = 10,
                          players_df=None) -> tuple:
    players = _resolve_players(players, players_df)

    if batting.empty:
        return pd.DataFrame(), go.Figure()

    # Column detect karo
    name_col = None
    for c in ("batsman_name", "batsman_id", "batsman"):
        if c in batting.columns:
            name_col = c
            break
    if name_col is None:
        return pd.DataFrame(), go.Figure()

    # ID hoy to name map karo
    if (name_col in ("batsman_id", "batsman")
            and players is not None
            and not players.empty
            and "player_id" in players.columns
            and "player_name" in players.columns):
        id_map = players.set_index("player_id")["player_name"].to_dict()
        batting = batting.copy()
        batting["batsman_display"] = (
            batting[name_col].map(id_map).fillna(batting[name_col].astype(str))
        )
        name_col = "batsman_display"

    # Aggregate
    agg_cols = {}
    if "runs"     in batting.columns: agg_cols["runs"]    = ("runs",     "sum")
    if "balls"    in batting.columns: agg_cols["balls"]   = ("balls",    "sum")
    if "Match ID" in batting.columns: agg_cols["matches"] = ("Match ID", "nunique")
    elif "match_id" in batting.columns: agg_cols["matches"] = ("match_id", "nunique")
    if "sixes"    in batting.columns: agg_cols["sixes"]   = ("sixes",    "sum")
    if "fours"    in batting.columns: agg_cols["fours"]   = ("fours",    "sum")

    df = (
        batting.groupby(name_col)
        .agg(**agg_cols)
        .reset_index()
        .rename(columns={name_col: "player_name"})
    )

    # Strike rate calculate karo
    if "runs" in df.columns and "balls" in df.columns:
        df["strike_rate"] = (
            df["runs"] / df["balls"].replace(0, pd.NA) * 100
        ).round(2)

    df = df.sort_values("runs", ascending=False).head(top_n).reset_index(drop=True)

    fig = px.bar(
        df,
        x="runs",
        y="player_name",
        orientation="h",
        color="strike_rate" if "strike_rate" in df.columns else "runs",
        color_continuous_scale="Oranges",
        labels={"runs": "Total Runs", "player_name": "Batsman", "strike_rate": "Strike Rate"},
        text="runs",
        hover_data=[c for c in ["matches", "sixes", "fours", "strike_rate"] if c in df.columns],
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        yaxis=dict(autorange="reversed"),
        coloraxis_showscale=True,
        template="plotly_dark",
        height=550,
        title={"text": "🏏 Highest Run-Scorers in ODI Internationals",
               "x": 0.5, "xanchor": "center"},
    )
    return df, fig

# ══════════════════════════════════════════════════════════════════════════════
# 5. Most sixes (by player) — ODI
# ══════════════════════════════════════════════════════════════════════════════
def analysis_most_sixes(batting: pd.DataFrame,
                         players=None,
                         top_n: int = 10,
                         players_df=None) -> tuple:
    players = _resolve_players(players, players_df)

    if batting.empty:
        return pd.DataFrame(), go.Figure()

    if "sixes" not in batting.columns:
        return pd.DataFrame(), go.Figure()

    name_col = None
    for c in ("batsman_name", "batsman_id", "batsman"):
        if c in batting.columns:
            name_col = c
            break
    if name_col is None:
        return pd.DataFrame(), go.Figure()

    # ID hoy to name map karo
    if (name_col in ("batsman_id", "batsman")
            and players is not None
            and not players.empty
            and "player_id" in players.columns
            and "player_name" in players.columns):
        id_map = players.set_index("player_id")["player_name"].to_dict()
        batting = batting.copy()
        batting["batsman_display"] = (
            batting[name_col].map(id_map).fillna(batting[name_col].astype(str))
        )
        name_col = "batsman_display"

    # Aggregate
    agg_cols = {"sixes": ("sixes", "sum")}
    if "Match ID"   in batting.columns: agg_cols["matches"] = ("Match ID",  "nunique")
    elif "match_id" in batting.columns: agg_cols["matches"] = ("match_id",  "nunique")

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
    fig.update_layout(
        yaxis=dict(autorange="reversed") if False else {},  
        title={"text": "💥 Players Who Hit Most Sixes in ODIs",
               "x": 0.5, "xanchor": "center"},
        template="plotly_dark",
        height=550,
        coloraxis_showscale=False,
    )
    return df, fig
# ══════════════════════════════════════════════════════════════════════════════
# 5b. Most sixes (by team)
# ══════════════════════════════════════════════════════════════════════════════
def analysis_team_sixes(batting: pd.DataFrame, top_n: int = 10) -> tuple:
    if batting.empty or 'team' not in batting.columns:
        return pd.DataFrame(), go.Figure()

    df = (batting.groupby('team')['sixes']
          .sum().reset_index()
          .sort_values('sixes', ascending=False)
          .head(top_n).reset_index(drop=True))

    fig = px.bar(
        df, x='team', y='sixes',
        color='sixes', color_continuous_scale='Purples', text='sixes',
    )
    fig.update_traces(textposition='inside', textfont=dict(color='white', size=12))
    fig.update_layout(
        title={'text': '💥 Teams That Hit Most Sixes — ODIs', 'x': 0.5, 'xanchor': 'center'},
        xaxis_title='Team', yaxis_title='Total Sixes',
        xaxis_tickangle=-45, coloraxis_showscale=False,
        template='plotly_dark', height=500,
    )
    return df, fig
# ══════════════════════════════════════════════════════════════════════════════
# 5c. Most fours (by player) — ODI
# ══════════════════════════════════════════════════════════════════════════════
def analysis_most_fours(batting: pd.DataFrame,
                         players=None,
                         top_n: int = 10,
                         players_df=None) -> tuple:
    players = _resolve_players(players, players_df)

    if batting.empty or "fours" not in batting.columns:
        return pd.DataFrame(), go.Figure()

    name_col = None
    for c in ("batsman_name", "batsman_id", "batsman"):
        if c in batting.columns:
            name_col = c
            break
    if name_col is None:
        return pd.DataFrame(), go.Figure()

    if (name_col in ("batsman_id", "batsman")
            and players is not None
            and not players.empty
            and "player_id" in players.columns
            and "player_name" in players.columns):
        id_map = players.set_index("player_id")["player_name"].to_dict()
        batting = batting.copy()
        batting["batsman_display"] = (
            batting[name_col].map(id_map).fillna(batting[name_col].astype(str))
        )
        name_col = "batsman_display"

    agg_cols = {"fours": ("fours", "sum")}
    if "Match ID"   in batting.columns: agg_cols["matches"] = ("Match ID",  "nunique")
    elif "match_id" in batting.columns: agg_cols["matches"] = ("match_id",  "nunique")

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
    fig.update_layout(
        title={"text": "4️⃣ Players Who Hit Most Fours in ODIs",
               "x": 0.5, "xanchor": "center"},
        template="plotly_dark",
        height=550,
        coloraxis_showscale=False,
    )
    return df, fig


# ══════════════════════════════════════════════════════════════════════════════
# 5d. Most fours (by team) — ODI
# ══════════════════════════════════════════════════════════════════════════════
def analysis_team_fours(batting: pd.DataFrame, top_n: int = 10) -> tuple:
    if batting.empty or "fours" not in batting.columns or "team" not in batting.columns:
        return pd.DataFrame(), go.Figure()

    df = (
        batting.groupby("team")["fours"]
        .sum().reset_index()
        .sort_values("fours", ascending=False)
        .head(top_n).reset_index(drop=True)
    )

    fig = px.pie(
        df, names="team", values="fours",
        color_discrete_sequence=px.colors.qualitative.Bold,
        hole=0.35,
    )
    fig.update_traces(texttemplate="%{label}<br>%{value}", textinfo="label+value")
    fig.update_layout(
        title={"text": "4️⃣ Fours Per Team in ODIs", "x": 0.5, "xanchor": "center"},
        template="plotly_dark",
        height=500,
    )
    return df, fig


# ══════════════════════════════════════════════════════════════════════════════
# 6. Most successful teams
# ══════════════════════════════════════════════════════════════════════════════
def analysis_successful_teams(matches: pd.DataFrame, top_n: int = 10) -> tuple:
    for col in ('Match Winner', 'winner', 'Winner', 'match_winner', 'winning_team'):
        if col in matches.columns:
            winner_col = col
            break
    else:
        return pd.DataFrame(), go.Figure()

    wins = matches[winner_col].dropna().value_counts().reset_index()
    wins.columns = ['team', 'wins']

    team1_col = 'Team1 Name' if 'Team1 Name' in matches.columns else None
    team2_col = 'Team2 Name' if 'Team2 Name' in matches.columns else None

    if team1_col and team2_col:
        t1 = matches[team1_col].value_counts().reset_index()
        t1.columns = ['team', 'c1']
        t2 = matches[team2_col].value_counts().reset_index()
        t2.columns = ['team', 'c2']
        played = t1.merge(t2, on='team', how='outer').fillna(0)
        played['matches_played'] = (played['c1'] + played['c2']).astype(int)
        played = played[['team', 'matches_played']]
    else:
        played = wins.rename(columns={'wins': 'matches_played'})

    df = wins.merge(played, on='team', how='left')
    df['win_pct'] = (df['wins'] / df['matches_played'] * 100).round(1)
    df = df.sort_values('wins', ascending=False).head(top_n).reset_index(drop=True)
    df = df[['team', 'wins', 'matches_played', 'win_pct']]

    fig = px.bar(
        df, x='team', y='wins',
        color='win_pct', color_continuous_scale='RdYlGn',
        text='win_pct', hover_data=['matches_played', 'wins', 'win_pct'],
    )
    fig.update_traces(
        texttemplate='%{text}%', textposition='inside',
        textfont=dict(color='white', size=12),
    )
    fig.update_layout(
        title={'text': '🏆 Most Successful Teams in ODI Internationals',
               'x': 0.5, 'xanchor': 'center'},
        xaxis_title='Team', yaxis_title='Total Wins',
        xaxis_tickangle=-45, template='plotly_dark', height=550,
    )
    return df, fig