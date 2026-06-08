"""
Run:  streamlit run app.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from streamlit_option_menu import option_menu
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings("ignore")
from utils.data_loader import load_t20
from utils.t20_analysis import (
      analysis_host_countries, analysis_man_of_match,
      analysis_wicket_takers, analysis_run_scorers,
      analysis_most_sixes, analysis_successful_teams,
      analysis_team_sixes,
      analysis_most_fours, analysis_team_fours,   # ← add karo
analysis_head_to_head,analysis_venue,analysis_career_arc   ,analysis_seasonal_trends ,analysis_batsman_bowler_matrix,analysis_ball_heatmap
  )

import streamlit as st
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.abspath("utils"))

from utils.odi_loader   import load_all
from utils.odi_analysis import (
    analysis_host_countries,
    analysis_wicket_takers,
    analysis_run_scorers,
    analysis_most_sixes,
    analysis_successful_teams,
)
from utils.data_loader import (
    load_matches, load_deliveries, merge_data,
    compute_batsman_stats, compute_bowler_stats,
    compute_team_stats, compute_nrr,
)
from utils.test_loader   import load_all_test_data
from utils.test_analysis import (
        get_matches_by_country, get_matches_by_venue,
        get_top_wicket_takers, get_top_run_scorers,
        get_team_rankings,
        get_dot_ball_by_bowler, get_dot_ball_by_team,
    )
from models.predictor import build_model, predict_winner

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CricketSphere",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main { background: #0d1117; }
.stApp { background: linear-gradient(135deg,#0d1117 0%,#161b22 100%); color:#e6edf3; }
.block-container { padding: 1.5rem 2rem; }

/* metric cards */
[data-testid="metric-container"] {
    background: linear-gradient(135deg,#1f2937,#111827);
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 1rem;
    box-shadow: 0 4px 20px rgba(0,0,0,.4);
}
[data-testid="metric-container"] label { color:#8b949e !important; font-size:.75rem; }
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color:#58a6ff !important; font-weight:700;
}
/* ── Sidebar background ── */
[data-testid="stSidebar"] > div:first-child {
    background-color: #1a1a2e !important;
}
[data-testid="stSidebar"] {
    background-color: #1a1a2e !important;
}

/* ── Title ── */
[data-testid="stSidebar"] h2 {
    color: #ffffff !important;
    font-size: 18px;
    font-weight: 700;
}

/* ── Hide radio circles completely ── */
[data-testid="stSidebar"] [role="radiogroup"] input[type="radio"] {
    display: none !important;
}
[data-testid="stSidebar"] [role="radiogroup"] [data-testid="stMarkdownContainer"] ~ div,
[data-testid="stSidebar"] .st-emotion-cache-ue6h4q {
    display: none !important;
}

/* ── Nav label styling ── */
[data-testid="stSidebar"] [role="radiogroup"] label {
    background: transparent !important;
    border-radius: 8px !important;
    padding: 9px 14px !important;
    font-size: 14px !important;
    color: #8888aa !important;
    width: 100% !important;
    transition: all 0.15s ease !important;
}

[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(255,255,255,0.06) !important;
    color: #ffffff !important;
}

/* ── Active/selected item ── */
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: rgba(255, 140, 0, 0.12) !important;
    color: #ff8c00 !important;
    font-weight: 600 !important;
    border-left: 3px solid #ff8c00 !important;
}

/* ── "Navigate" label ── */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label {
    color: #8888aa !important;
}

/* ── Divider ── */
[data-testid="stSidebar"] hr {
    border-color: #2e2e4a !important;
}

/* ── Caption ── */
[data-testid="stSidebar"] .stCaption p {
    color: #555577 !important;
    font-size: 11.5px !important;
}

/* ── Scrollbar ── */
[data-testid="stSidebar"]::-webkit-scrollbar { width: 3px; }
[data-testid="stSidebar"]::-webkit-scrollbar-track { background: #1a1a2e; }
[data-testid="stSidebar"]::-webkit-scrollbar-thumb { 
    background: #2e2e4a; 
    border-radius: 4px; 
}

/* sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#161b22 0%,#0d1117 100%) !important;
    border-right: 1px solid #30363d;
}
[data-testid="stSidebar"] * { color:#e6edf3 !important; }

/* headers */
h1,h2,h3 { color:#f0f6fc !important; }
h1 { background: linear-gradient(90deg,#f97316,#ef4444); -webkit-background-clip:text;
     -webkit-text-fill-color:transparent; font-weight:900; }

/* tabs */
.stTabs [data-baseweb="tab-list"] { background:#161b22; border-radius:10px; padding:4px; gap:4px; }
.stTabs [data-baseweb="tab"] { background:transparent; color:#8b949e !important; border-radius:8px; }
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background:linear-gradient(135deg,#f97316,#ef4444) !important;
    color:#fff !important; font-weight:600;
}

/* selectbox */
.stSelectbox>div>div { background:#1f2937 !important; border:1px solid #30363d !important; color:#e6edf3 !important; }

/* divider */
hr { border-color:#30363d; }

.section-header {
    font-size:1.3rem; font-weight:700; color:#f0f6fc;
    padding:.5rem 0; border-bottom:2px solid #f97316;
    margin-bottom:1rem;
}
</style>
""", unsafe_allow_html=True)
# ── Cache so data loads once ─────────────────────────────
@st.cache_data
def get_odi_data():
    return load_all()
 
 
def render_odi_tab():
    """
    Call this function inside  `with tab_odi:`  in your app.py
    """
    st.header("🏏 ODI International Cricket Analysis")
 
    data    = get_odi_data()
    matches = data["matches"]
    batting = data["batting"]
    bowling = data["bowling"]
    players = data["players"]
# ── data loading (cached) ─────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading IPL data…")
def get_data():
    matches    = load_matches()
    deliveries = load_deliveries()
    merged     = merge_data(matches, deliveries)
    bat_stats  = compute_batsman_stats(deliveries)
    bowl_stats = compute_bowler_stats(deliveries)
    team_stats = compute_team_stats(matches)
    return matches, deliveries, merged, bat_stats, bowl_stats, team_stats

matches, deliveries, merged, bat_stats, bowl_stats, team_stats = get_data()

# ── Real IPL win percentages (override synthetic data) ────────────────────────
REAL_WIN_PCT = {
    "Chennai Super Kings":          57.7,
    "Mumbai Indians":               54.4,
    "Kolkata Knight Riders":        51.6,
    "Rajasthan Royals":             49.8,
    "Sunrisers Hyderabad":          47.8,
    "Royal Challengers Bangalore":  47.2,
    "Delhi Capitals":               44.4,
    "Punjab Kings":                 44.3,
    "Gujarat Titans":               58.3,
    "Lucknow Super Giants":         54.5,
}
team_stats["win_pct"] = team_stats["team"].map(REAL_WIN_PCT).fillna(team_stats["win_pct"])
team_stats = team_stats.sort_values("win_pct", ascending=False).reset_index(drop=True)

SEASONS = sorted(matches["season"].unique())
TEAMS   = sorted(matches["team1"].dropna().unique())
PLAYERS = sorted(set(bat_stats["player"].tolist() + bowl_stats["player"].tolist()))
from streamlit_option_menu import option_menu

with st.sidebar:

    st.markdown("""
    <div style='text-align:center;padding-bottom:10px;'>
        <h2>🏏 CricketSphere</h2>
        <p style='color:#8b949e;font-size:12px;'>
        Cricket Analytics Platform
        </p>
    </div>
    """, unsafe_allow_html=True)

    selected = option_menu(
        menu_title="Navigation",
        options=[
    "🏏 IPL Analytics",
    "⚡ T20I Analytics",
    "🌍 ODI Analytics",
    "🎩 Test Analytics"
],
        icons=[
            "trophy-fill",
            "lightning-fill",
            "globe-central-south-asia",
            "activity"
        ],
        menu_icon="bar-chart-fill",
        default_index=0,

        styles={
            "container": {
                "padding": "8px",
                "background-color": "#161b22",
                "border-radius": "12px",
                "border": "1px solid #30363d",
            },

            "icon": {
                "color": "#f97316",
                "font-size": "18px"
            },

            "nav-link": {
                "font-size": "15px",
                "text-align": "left",
                "margin": "4px 0",
                "padding": "10px",
                "border-radius": "10px",
                "color": "#e6edf3",
                "--hover-color": "#21262d",
            },

            "nav-link-selected": {
                "background":
                "linear-gradient(135deg,#f97316,#ef4444)",
                "color": "white",
                "font-weight": "600",
            },

            "menu-title": {
                "font-size": "18px",
                "font-weight": "700",
                "color": "#ffffff",
            }
        }
    )
    

m = matches
d = deliveries

# ── helper: plotly dark layout ────────────────────────────────────────────────
DARK = dict(
    plot_bgcolor="#161b22",
    paper_bgcolor="#0d1117",
    font_color="#e6edf3",
    xaxis=dict(gridcolor="#21262d", linecolor="#30363d"),
    yaxis=dict(gridcolor="#21262d", linecolor="#30363d"),
)
PALETTE = px.colors.qualitative.Bold

def dark_fig(fig):
    fig.update_layout(**DARK, margin=dict(l=20,r=20,t=40,b=20))
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# IPL PAGE
# ══════════════════════════════════════════════════════════════════════════════
# app.py ma IPL section ma sirf aa lakhvu:

from utils.ipl_analysis import render_ipl_tab

# ... (sidebar and other format code same raheshe)

if selected == "🏏 IPL Analytics":
    render_ipl_tab(
        matches, deliveries, bat_stats, bowl_stats, team_stats,
        SEASONS, TEAMS, PALETTE, dark_fig, DARK,
        build_model, predict_winner
    )

# ══════════════════════════════════════════════════════════════════════════════
# PAGE – T20 RANKINGS  (T20 International Analytics)
# ══════════════════════════════════════════════════════════════════════════════

 
elif selected == "⚡ T20I Analytics":
    st.markdown("""
        <style>
        .main-title {
            font-size: 40px;
            font-weight: 800;
            color: #7c3aed;
            text-align: center;
            margin-bottom: 0;
        }
    
        .sub-title {
            text-align: center;
            color: #bbbbbb;
            font-size: 18px;
            margin-top: -10px;
            margin-bottom: 25px;
        }
    
        .metric-card {
            background: linear-gradient(135deg, #1f1f1f, #2b2b2b);
            padding: 18px;
            border-radius: 18px;
            text-align: center;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.08);
        }
    
        .metric-value {
            font-size: 28px;
            font-weight: 700;
            color: white;
        }
    
        .metric-label {
            font-size: 15px;
            color: #cfcfcf;
        }
        </style>
        """, unsafe_allow_html=True)
    
        # ================= TITLE =================
    st.markdown(
            f"""
            <div class="main-title"> T20 International Rankings & Analysis</div>
            <div class="sub-title">
            T20 Cricket Matches • 2005 - 2024 • Complete Analysis
            </div>
            """,
            unsafe_allow_html=True
        )
    
    
    # ── load T20I data (cached) ───────────────────────────────────────────────
    @st.cache_data(show_spinner="Loading T20I data…")
    def get_t20_data():
        from utils.data_loader import load_t20
        return load_t20()
 
    try:
        t20 = get_t20_data()
        t20_matches      = t20["matches"]
        t20_batting      = t20["batting"]
        t20_bowling      = t20["bowling"]
        t20_players      = t20["players"]
    except Exception as e:
        st.error(f"Could not load T20I data: {e}")
        st.info("Make sure the T20I CSVs are in the /data folder.")
        st.stop()
 
    from utils.t20_analysis import (
        analysis_host_countries, analysis_man_of_match,
        analysis_wicket_takers, analysis_run_scorers,
        analysis_most_sixes, analysis_successful_teams,
        analysis_team_sixes,
    )
 
 
    st.markdown("""
    <style>
    /* ── Center tablist ── */
    [data-testid="stTabs"] [role="tablist"] {
        justify-content: center !important;
        gap: 6px !important;
        border-bottom: none !important;
        flex-wrap: wrap !important;
    }
    
    /* ── All tabs base ── */
    [data-testid="stTabs"] [role="tab"] {
        font-size: 12px !important;
        font-weight: 500 !important;
        padding: 8px 14px !important;
        border-radius: 10px !important;
        color: #aaaaaa !important;
        background: #2a2a2a !important;
        border: none !important;
        transition: all 0.2s ease !important;
        white-space: nowrap !important;
    }
    
    /* ── Hover ── */
    [data-testid="stTabs"] [role="tab"]:hover {
        background: #333333 !important;
        color: #ffffff !important;
    }
    
    /* ── Active tab — filled orange ── */
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        background: #ff8c00 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-bottom: none !important;
        box-shadow: 0 2px 12px rgba(255, 140, 0, 0.3) !important;
    }
    
    /* ── Remove default underline indicator ── */
    [data-testid="stTabs"] [role="tab"][aria-selected="true"]::before,
    [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        display: none !important;
        background: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    tabs = st.tabs([
        "Countries & Venues",
        "Wicket Takers",
        "Run Scorers",
        "Sixes & Fours",
        "Team Rankings",
        "Advanced Insights",

    ])
 
 
    # 1. Host Countries + Venue Analysis
    with tabs[0]:
    
        # ── Host Countries ────────────────────────────────────────────
        # st.markdown("#### 🌍 Host Countries")
        df_host, fig_host = analysis_host_countries(t20_matches, top_n=10)
        st.plotly_chart(fig_host, use_container_width=True)
        # st.dataframe(df_host, use_container_width=True, hide_index=True)
    
        st.divider()
    
        # ── Venue Analysis ────────────────────────────────────────────
        st.markdown("####  Venue Analysis")
        venue_df, _, _ = analysis_venue(t20_matches)
    
        if venue_df.empty:
            st.warning("Venue data available nathi.")
        else:
            # Venue selector (Stadium + City + Country)
            venue_display = []
            for _, row in venue_df.iterrows():
                country = f" ({row['country']})" if "country" in venue_df.columns and pd.notna(row.get("country")) else ""
                city    = f", {row['city']}"     if "city"    in venue_df.columns and pd.notna(row.get("city"))    else ""
                venue_display.append(f"{row['venue']}{city}{country}")
    
            selected_display = st.selectbox("Venue select ", venue_display, key="venue_sel")
            selected = venue_df.iloc[venue_display.index(selected_display)]["venue"]
    
            _, vstats, figs = analysis_venue(t20_matches, selected_venue=selected)
    
            # KPI strip
            if vstats:
                k1, k2, k3, k4, k5, k6 = st.columns(6)
                k1.metric("Matches",         vstats["matches"])
                k2.metric("Highest Score",   vstats["highest"])
                k3.metric("Lowest Score",    vstats["lowest"])
                k4.metric("Avg 1st Innings", f"{vstats['avg_1st']}")
                k5.metric("Chasing Win %",   f"{vstats['chase_win_pct']}%")
                k6.metric("Toss Impact %",   f"{vstats['toss_impact_pct']}%")
    
            st.divider()
    
            # Charts
            if figs:
                st.plotly_chart(figs[0], use_container_width=True, key="venue_fig1")
            if len(figs) > 1:
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(figs[1], use_container_width=True, key="venue_fig2")
                with col2:
                    if len(figs) > 2:
                        st.plotly_chart(figs[2], use_container_width=True, key="venue_fig3")
    
            st.divider()
    
            # Full venue table
            st.markdown("#### All Venues Summary")
            show_cols = [c for c in [
                "venue", "city", "country", "matches",
                "highest", "lowest", "avg_1st", "avg_2nd",
                "chase_win_pct", "toss_impact_pct"
            ] if c in venue_df.columns]
            st.dataframe(venue_df[show_cols], use_container_width=True, hide_index=True)
            
#     # 2. Man of the Match
#     with tabs[1]:
#         # st.markdown("### Top Players with Most Man-of-the-Match Awards")
#         # n = st.slider("Top N players", 5, 20, 10, key="mom_n")
#         df, fig = analysis_man_of_match(t20_matches, t20_players, top_n=10)
#         st.plotly_chart(
#     fig,
#     use_container_width=True,
#     key="unique_chart_1674"
# )
#         st.dataframe(df, use_container_width=True, hide_index=True)
 
    # 3. Wicket takers
    with tabs[1]:
        # st.markdown("### Highest Wicket-Takers in T20 Internationals")
        # n = st.slider("Top N bowlers", 5, 20, 10, key="wkt_n")
        df, fig = analysis_wicket_takers(t20_bowling, t20_players, top_n=12)
        st.plotly_chart(fig, use_container_width=True)
        if not df.empty:
            # Scatter: economy vs wickets
            hover_cols = [c for c in ["matches", "economy", "runs_conceded"] if c in df.columns]
            fig2 = px.scatter(
                df, x="economy", y="wickets", text="player",
                size="matches" if "matches" in df.columns else None,
                color="economy", color_continuous_scale="RdYlGn_r",
                hover_data=hover_cols,
                labels={"economy": "Economy Rate", "wickets": "Wickets"},
                title="Economy Rate vs Wickets",
            )
            fig2.update_traces(textposition="top center")
            fig2.update_layout(
                plot_bgcolor="#161b22", paper_bgcolor="#0d1117",
                font_color="#e6edf3", margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
 
    # 4. Run scorers
    with tabs[2]:
        # st.markdown("### Highest Run-Scorers in T20 Internationals")
        # n = st.slider("Top N batsmen", 5, 20, 10, key="run_n")
        df, fig = analysis_run_scorers(t20_batting, t20_players, top_n=12)
        st.plotly_chart(fig, use_container_width=True)
        
        from utils.t20_analysis import analysis_career_arc

        st.caption("Season-by-season batting & bowling journey — peak years, slumps & comebacks")
     
        # ── Controls row ─────────────────────────────────────────────────────────────
        col1, col2, col3 = st.columns([2, 1, 1])
         
        with col1:
            # Build player list from players_info
            all_players = sorted(t20_players["player_name"].dropna().unique().tolist())
            selected_player = st.selectbox(
                "Select player",
                options=all_players,
                index=0,
                key="career_arc_player",
            )
         
        with col2:
            mode = st.radio(
                "Mode",
                options=["Batting", "Bowling"],
                horizontal=True,
                key="career_arc_mode",
            )
         
         
        # ── Run analysis ─────────────────────────────────────────────────────────────
        arc_df, figs = analysis_career_arc(
            batting      = t20_batting,
            bowling      = t20_bowling,
            players      = t20_players,
            matches      = t20_matches,
            player_name  = selected_player,
            mode         = mode.lower(),
        )
         
         
        # ── No data guard ─────────────────────────────────────────────────────────────
        if arc_df.empty:
            st.warning(
                f"No T20I {mode.lower()} data found for **{selected_player}**. "
                "Try a different player or mode."
            )
            st.stop()
         
        # ── Summary metric cards ──────────────────────────────────────────────────────
        st.markdown("---")
         
        if mode == "Batting":
            total_runs    = int(arc_df["runs"].sum())
            total_matches = int(arc_df["matches"].sum())
            avg_sr        = round(arc_df["strike_rate"].mean(), 1)
            peak_season   = arc_df.loc[arc_df["runs"].idxmax(), "season"]
            peak_runs     = int(arc_df["runs"].max())
            career_span   = f"{int(arc_df['season'].min())} – {int(arc_df['season'].max())}"
         
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Career span",   career_span)
            m2.metric("Total runs",    f"{total_runs:,}")
            m3.metric("Matches",       total_matches)
            m4.metric("Avg SR",        avg_sr)
            m5.metric("Peak season",   f"{peak_season} ({peak_runs} runs)")
         
        else:
            total_wkts    = int(arc_df["wickets"].sum())
            total_matches = int(arc_df["matches"].sum())
            avg_econ      = round(arc_df["economy"].mean(), 2)
            peak_season   = arc_df.loc[arc_df["wickets"].idxmax(), "season"]
            peak_wkts     = int(arc_df["wickets"].max())
            career_span   = f"{int(arc_df['season'].min())} – {int(arc_df['season'].max())}"
         
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Career span",   career_span)
            m2.metric("Total wickets", total_wkts)
            m3.metric("Matches",       total_matches)
            m4.metric("Avg economy",   avg_econ)
            m5.metric("Peak season",   f"{peak_season} ({peak_wkts} wkts)")
         
        # ── Charts ────────────────────────────────────────────────────────────────────
        st.markdown("---")
         
        if figs and len(figs) >= 1:
            st.plotly_chart(figs[0], use_container_width=True)   # Runs / Wickets arc
         
        if figs and len(figs) >= 2:
            st.plotly_chart(figs[1], use_container_width=True)   # SR / Economy arc
         
        # ── Raw season table (collapsible) ───────────────────────────────────────────
        with st.expander("View season-by-season data table"):
            display_df = arc_df.copy()
            display_df["season"] = display_df["season"].astype(int)
         
            if mode == "Batting":
                display_df = display_df.rename(columns={
                    "season": "Season", "runs": "Runs", "balls": "Balls",
                    "sixes": "6s", "fours": "4s", "matches": "Matches",
                    "strike_rate": "Strike Rate", "avg_per_match": "Avg/Match",
                })
                col_order = ["Season", "Matches", "Runs", "Balls", "Strike Rate", "Avg/Match", "6s", "4s"]
            else:
                display_df = display_df.rename(columns={
                    "season": "Season", "wickets": "Wickets", "runs_conceded": "Runs Conceded",
                    "overs": "Overs", "matches": "Matches", "economy": "Economy", "avg": "Bowling Avg",
                })
                col_order = ["Season", "Matches", "Wickets", "Overs", "Runs Conceded", "Economy", "Bowling Avg"]
         
            cols_present = [c for c in col_order if c in display_df.columns]
            st.dataframe(
                display_df[cols_present].reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
            )
     
            # st.dataframe(df, use_container_width=True, hide_index=True)
     
    # 5. Sixes & Fours
    with tabs[3]:
        # ── By Player ─────────────────────────────────────────────
        # st.markdown("#### By Player")
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("##### 💥 Most Sixes")
            df_six, fig_six = analysis_most_sixes(t20_batting, t20_players, top_n=10)
            st.plotly_chart(fig_six, use_container_width=True)
            # st.dataframe(df_six, use_container_width=True, hide_index=True)
        with col_r:
            st.markdown("##### 4️⃣ Most Fours")
            df_four, fig_four = analysis_most_fours(t20_batting, t20_players, top_n=10)
            st.plotly_chart(fig_four, use_container_width=True)
            # st.dataframe(df_four, use_container_width=True, hide_index=True)

        st.divider()

        # ── By Team ───────────────────────────────────────────────
        # st.markdown("#### By Team")
        col_l2, col_r2 = st.columns(2)
        with col_l2:
            st.markdown("##### 💥 Sixes Per Team")
            df_tsix, fig_tsix = analysis_team_sixes(t20_batting, top_n=10)
            st.plotly_chart(fig_tsix, use_container_width=True)
            # st.dataframe(df_tsix, use_container_width=True, hide_index=True)
        with col_r2:
            st.markdown("##### 4️⃣ Fours Per Team")
            df_tfour, fig_tfour = analysis_team_fours(t20_batting, top_n=10)
            st.plotly_chart(fig_tfour, use_container_width=True)
            # st.dataframe(df_tfour, use_container_width=True, hide_index=True)
 
    # 6. Team rankings
    with tabs[4]:
        st.markdown("### Most Successful Teams in T20Is")
        # n = st.slider("Top N teams", 5, 20, 10, key="team_n")
        df, fig = analysis_successful_teams(t20_matches, top_n=10)
        st.plotly_chart(
    fig,
    use_container_width=True,
    key="chart_1749"
)
 
        if not df.empty and "win_pct" in df.columns:
            fig2 = px.treemap(
                df, path=["team"], values="wins",
                color="win_pct", color_continuous_scale="RdYlGn",
                hover_data=["played", "wins", "win_pct"],
                title="Win % Treemap",
            )
            fig2.update_layout(paper_bgcolor="#0d1117", font_color="#e6edf3")
            st.plotly_chart(fig2, use_container_width=True)
 
        st.dataframe(df, use_container_width=True, hide_index=True)
    

# 8. 🔥 Advanced Analysis  
    with tabs[5]:

        # st.markdown("##  Advanced Analysis")

        subtabs = st.tabs([
        " Head-to-Head",
        " Ball Heatmap",
        " Matchups",
        " Seasonal Trends"
    ])

        # ──────────────────────────────────────────────
        # HEAD TO HEAD
        # ──────────────────────────────────────────────
        with subtabs[0]:
        
            st.markdown("####  Head-to-Head Analysis")
        
            all_teams = sorted(set(
                t20_matches.get("Team1 Name", pd.Series()).dropna().tolist() +
                t20_matches.get("Team2 Name", pd.Series()).dropna().tolist()
            ))
        
            col_a, col_b = st.columns(2)
        
            team_a = col_a.selectbox(
                "Team A",
                all_teams,
                key="h2h_a"
            )
        
            team_b = col_b.selectbox(
                "Team B",
                [t for t in all_teams if t != team_a],
                key="h2h_b"
            )
        
            df_h2h, stats = analysis_head_to_head(
                t20_matches,
                t20_players,
                team_a,
                team_b
            )
        
            if not stats:
                st.warning(
                    f"No matches found between {team_a} and {team_b}."
                )
        
            else:
        
                k1, k2, k3, k4, k5 = st.columns(5)
        
                k1.metric("Total Matches", stats["total"])
        
                k2.metric(
                    f"{team_a} Wins",
                    f"{stats['wins_a']} ({stats['pct_a']}%)"
                )
        
                k3.metric(
                    f"{team_b} Wins",
                    f"{stats['wins_b']} ({stats['pct_b']}%)"
                )
        
                k4.metric(
                    "Draws / NR",
                    stats["draws"]
                )
        
                k5.metric(
                    "Highest Score",
                    stats["highest"] or "—"
                )
        
                fig_bar = go.Figure(
                    go.Bar(
                        x=[
                            stats["wins_a"],
                            stats["draws"],
                            stats["wins_b"]
                        ],
                        y=[
                            team_a,
                            "Draw/NR",
                            team_b
                        ],
                        orientation="h",
                        text=[
                            f"{stats['pct_a']}%",
                            "",
                            f"{stats['pct_b']}%"
                        ],
                        textposition="inside",
                    )
                )
        
                fig_bar.update_layout(
                    template="plotly_dark",
                    height=250,
                    title=f"{team_a} vs {team_b}"
                )
        
                st.plotly_chart(
                    fig_bar,
                    use_container_width=True
                )
        
                st.markdown("#### Recent 5 Matches")
        
                display_cols = [
                    c for c in [
                        "Match Date",
                        "Team1 Name",
                        "Team1 Runs Scored",
                        "Team2 Name",
                        "Team2 Runs Scored",
                        "Match Winner",
                        "Match Result Text"
                    ]
                    if c in df_h2h.columns
                ]
        
                st.dataframe(
                    df_h2h[display_cols].head(5),
                    use_container_width=True,
                    hide_index=True
                )
        
                with st.expander("View full match history"):
                    st.dataframe(
                        df_h2h[display_cols],
                        use_container_width=True,
                        hide_index=True
                    )
        # ──────────────────────────────────────────────────────────────
        # A) BALL HEATMAP
        # ──────────────────────────────────────────────────────────────
        with subtabs[1]:
   
            st.markdown("####  Ball-by-Ball Heatmap")
   
            col1, col2, col3 = st.columns(3)
   
            with col1:
                hm_mode = st.selectbox(
                    "Mode",
                    ["batting", "bowling"],
                    key="hm_mode",
                )
            with col2:
                all_players_hm = [""] + sorted(t20_players["player_name"].dropna().unique().tolist())
                hm_player = st.selectbox(
                    "Select Player",
                    options=all_players_hm,
                    format_func=lambda x: "All Players" if x == "" else x,
                    key="hm_player",
                )
            with col3:
                all_teams_hm = [""] + sorted(set(
                    t20_matches["Team1 Name"].dropna().unique().tolist() +
                    t20_matches["Team2 Name"].dropna().unique().tolist()
                ))
                hm_team = st.selectbox(
                    "Team filter (optional)",
                    options=all_teams_hm,
                    format_func=lambda x: "All Teams" if x == "" else x,
                    key="hm_team",
                )
   
            if st.button("Heatmap Generate ", key="hm_btn"):
                with st.spinner("Generating heatmap..."):
                    hm_df, hm_figs = analysis_ball_heatmap(
                        batting   = t20_batting,
                        bowling   = t20_bowling,
                        players   = t20_players,
                        matches   = t20_matches,
                        mode      = hm_mode,
                        player_name = hm_player.strip() or None,
                        team      = hm_team.strip() or None,
                    )
   
                if not hm_figs:
                    st.warning("No data found. Please check the player name or team selection.")
                else:
                    for i, fig in enumerate(hm_figs):
                        st.plotly_chart(fig, use_container_width=True, key=f"hm_fig_{i}")
   
                    if not hm_df.empty:
                        st.divider()
                        st.markdown("##### Summary Table")
                        st.dataframe(hm_df, use_container_width=True, hide_index=True)
   
        # ──────────────────────────────────────────────────────────────
        # B) BATSMAN–BOWLER MATRIX
        # ──────────────────────────────────────────────────────────────
        with subtabs[2]:
            st.markdown("####  Batsman–Bowler Interaction Matrix")
   
            col1, col2, col3 = st.columns(3)
   
            with col1:
                bb_metric = st.selectbox(
                    "Metric",
                    ["runs", "sr", "dismissal_pct"],
                    format_func=lambda x: {
                        "runs": "Total Runs",
                        "sr": "Strike Rate",
                        "dismissal_pct": "Dismissal %",
                    }[x],
                    key="bb_metric",
                )
            with col2:
                bb_top_bat = st.slider("Top N Batsmen", 5, 20, 10, key="bb_top_bat")
            with col3:
                bb_top_bowl = st.slider("Top N Bowlers", 5, 20, 10, key="bb_top_bowl")
   
            if st.button("Matrix Generate ", key="bb_btn"):
                with st.spinner("Generating matchup matrix..."):
                    bb_pivot, bb_fig = analysis_batsman_bowler_matrix(
                        batting    = t20_batting,
                        bowling    = t20_bowling,
                        players    = t20_players,
                        metric     = bb_metric,
                        top_n_bat  = bb_top_bat,
                        top_n_bowl = bb_top_bowl,
                    )
   
                if bb_pivot.empty:
                    st.warning("Unable to generate the matrix. Please check whether the required match_id and innings columns are available.")
                else:
                    st.plotly_chart(bb_fig, use_container_width=True, key="bb_fig")
   
                    st.divider()
                    st.markdown("##### Pivot Table")
                    st.dataframe(bb_pivot, use_container_width=True)
   
        # ──────────────────────────────────────────────────────────────
        # C) SEASONAL TRENDS
        # ──────────────────────────────────────────────────────────────
        with subtabs[3]:
    
            st.markdown("####  Seasonal Trends Dashboard")
   
            col1, col2 = st.columns(2)
   
            with col1:
                st_entity_type = st.selectbox(
                    "Entity Type",
                    ["player", "team"],
                    key="st_entity_type",
                )
                st_entity_name = st.text_input(
                    "Player / Team name",
                    value="",
                    key="st_entity_name",
                )
   
            with col2:
                st_metric = st.selectbox(
                    "Metric",
                    ["runs", "sr", "sixes", "fours", "wickets", "economy"],
                    format_func=lambda x: {
                        "runs":    "Runs",
                        "sr":      "Strike Rate",
                        "sixes":   "Sixes",
                        "fours":   "Fours",
                        "wickets": "Wickets",
                        "economy": "Economy Rate",
                    }[x],
                    key="st_metric",
                )
                st_window = st.slider(
                    "Moving Avg Window (seasons)",
                    2, 5, 3,
                    key="st_window",
                )
   
            if st.button("View Trends", key="st_btn"):
                if not st_entity_name.strip():
                    st.warning("Please enter a player or team name.")
                else:
                    with st.spinner("Calculating seasonal trends..."):
                        st_df, st_figs = analysis_seasonal_trends(
                            batting     = t20_batting,
                            bowling     = t20_bowling,
                            players     = t20_players,
                            matches     = t20_matches,
                            entity_type = st_entity_type,
                            entity_name = st_entity_name.strip(),
                            metric      = st_metric,
                            window      = st_window,
                        )
   
                    if not st_figs:
                        st.warning("No data found. Please check the selected name and metric.")
                    else:
                        for i, fig in enumerate(st_figs):
                            st.plotly_chart(fig, use_container_width=True, key=f"st_fig_{i}")
   
                        if not st_df.empty:
                            st.divider()
                            st.markdown("##### Season-wise Data")
   
                            # Anomaly rows highlight
                            def _highlight(row):
                                if row.get("anomaly_type") == "spike":
                                    return ["background-color: rgba(216,90,48,0.20)"] * len(row)
                                elif row.get("anomaly_type") == "slump":
                                    return ["background-color: rgba(155,89,182,0.20)"] * len(row)
                                return [""] * len(row)
   
                            show_cols = [c for c in [
                                "season", "value", "ma", "z_score", "anomaly_type"
                            ] if c in st_df.columns]
   
                            st.dataframe(
                                st_df[show_cols].style.apply(_highlight, axis=1),
                                use_container_width=True,
                                hide_index=True,
                            )
                    
        
# ──  ───────────────────────────────────────────────────────────────────────────
# OD  I Rankings page  —  fully fixed version
# Paste this block into app.py where the ODI page was.
# ─────────────────────────────────────────────────────────────────────────────
elif selected == "🌍 ODI Analytics":
    st.markdown("""
        <style>
        .main-title {
            font-size: 40px;
            font-weight: 800;
            color: #1565C0; 
            text-align: center;
            margin-bottom: 0;
        }
    
        .sub-title {
            text-align: center;
            color: #bbbbbb;
            font-size: 18px;
            margin-top: -10px;
            margin-bottom: 25px;
        }
    
        .metric-card {
            background: linear-gradient(135deg, #1f1f1f, #2b2b2b);
            padding: 18px;
            border-radius: 18px;
            text-align: center;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.08);
        }
    
        .metric-value {
            font-size: 28px;
            font-weight: 700;
            color: white;
        }
    
        .metric-label {
            font-size: 15px;
            color: #cfcfcf;
        }
        </style>
        """, unsafe_allow_html=True)
    
        # ================= TITLE =================
    st.markdown(
            f"""
            <div class="main-title">ODI International Rankings & Analysis</div>
            <div class="sub-title">
            ODI Cricket Matches • 1971 - 2024 • Complete Analysis
            </div>
            """,
            unsafe_allow_html=True
        )
    
    
    @st.cache_data(show_spinner="Loading ODI data…")
    def get_odi_data():
        from utils.odi_loader import load_all
        return load_all()
 
    try:
        odi         = get_odi_data()
        odi_matches = odi["matches"]
        odi_batting = odi["batting"]
        odi_bowling = odi["bowling"]
        odi_players = odi["players"]
    except Exception as e:
        st.error(f"Could not load ODI data: {e}")
        st.info("Make sure the ODI CSVs are in the /data folder.")
        st.stop()
 
    from utils.odi_analysis import (
        analysis_host_countries,
        analysis_wicket_takers,
        analysis_run_scorers,
        analysis_most_sixes,
        analysis_successful_teams,
        analysis_most_fours, analysis_team_fours,   
        analysis_venue

    )
 
 
 
    # ── Tab styling (blue for ODI) ─────────────────────────────────────
    st.markdown("""
<style>
[data-testid="stTabs"] [role="tablist"] {
    justify-content: center !important;
    gap: 10px !important;
    border-bottom: none !important;
}
[data-testid="stTabs"] [role="tab"] {
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 10px 24px !important;
    border-radius: 10px !important;
    color: #aaaaaa !important;
    background: #2a2a2a !important;
    border: none !important;
    transition: all 0.2s ease !important;
}
[data-testid="stTabs"] [role="tab"]:hover {
    background: #333333 !important;
    color: #ffffff !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: #1565C0 !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border-bottom: none !important;
    box-shadow: 0 2px 12px rgba(21,101,192,0.35) !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]::before,
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    display: none !important;
    background: transparent !important;
}
</style>
""", unsafe_allow_html=True)
 
    tabs = st.tabs([
        " Countries & Venues",   
        " Wicket Takers",
        " Run Scorers",
        " Sixes & Fours",
        " Team Rankings",
    ])
 
    with tabs[0]:
        # st.markdown("####  Host Countries")
        df_host, fig_host = analysis_host_countries(odi_matches, top_n=10)
        st.plotly_chart(fig_host, use_container_width=True)
        # st.dataframe(df_host, use_container_width=True, hide_index=True)
    
        st.divider()
    
        st.markdown("#### 🏟️ Venue Analysis")
        venue_df, _, _ = analysis_venue(odi_matches)
    
        if venue_df.empty:
            st.warning("Venue data available nathi.")
        else:
            venue_display = []
            for _, row in venue_df.iterrows():
                country = f" ({row['country']})" if "country" in venue_df.columns and pd.notna(row.get("country")) else ""
                city    = f", {row['city']}"     if "city"    in venue_df.columns and pd.notna(row.get("city"))    else ""
                venue_display.append(f"{row['venue']}{city}{country}")
    
            selected_display = st.selectbox("Venue select karo", venue_display, key="odi_venue_sel")  # ← key alag
            selected = venue_df.iloc[venue_display.index(selected_display)]["venue"]
    
            _, vstats, figs = analysis_venue(odi_matches, selected_venue=selected)
    
            if vstats:
                k1, k2, k3, k4, k5, k6 = st.columns(6)
                k1.metric("Matches",         vstats["matches"])
                k2.metric("Highest Score",   vstats["highest"])
                k3.metric("Lowest Score",    vstats["lowest"])
                k4.metric("Avg 1st Innings", f"{vstats['avg_1st']}")
                k5.metric("Chasing Win %",   f"{vstats['chase_win_pct']}%")
                k6.metric("Toss Impact %",   f"{vstats['toss_impact_pct']}%")
    
            st.divider()
    
            if figs:
                st.plotly_chart(figs[0], use_container_width=True, key="odi_venue_fig1")
            if len(figs) > 1:
                col1, col2 = st.columns(2)
                with col1:
                    st.plotly_chart(figs[1], use_container_width=True, key="odi_venue_fig2")
                with col2:
                    if len(figs) > 2:
                        st.plotly_chart(figs[2], use_container_width=True, key="odi_venue_fig3")
    
            st.divider()
    
            st.markdown("#### All Venues Summary")
            show_cols = [c for c in [
                "venue", "city", "country", "matches",
                "highest", "lowest", "avg_1st", "avg_2nd",
                "chase_win_pct", "toss_impact_pct"
            ] if c in venue_df.columns]
            st.dataframe(venue_df[show_cols], use_container_width=True, hide_index=True)
     
     
    # ── TAB 3 : Wicket takers ─────────────────────────────────────────
    with tabs[1]:
        # st.markdown("### Highest Wicket-Takers in ODI Internationals")
        # n = st.slider("Top N bowlers", 5, 20, 10, key="odi_wkt_n")
        df, fig = analysis_wicket_takers(odi_bowling, players_df=odi_players, top_n=12)
        st.plotly_chart(fig, use_container_width=True, key="odi_wkt_chart")
        if not df.empty:
            # Scatter: economy vs wickets
            hover_cols = [c for c in ["matches", "avg_economy", "runs_conceded"] if c in df.columns]
            fig2 = px.scatter(
                df, x="avg_economy", y="wickets", text="player",
                size="matches" if "matches" in df.columns else None,
                color="avg_economy", color_continuous_scale="RdYlGn_r",
                hover_data=hover_cols,
                labels={"avg_economy": "Economy Rate", "wickets": "Wickets"},
                title="Economy Rate vs Wickets",
            )
            fig2.update_traces(textposition="top center")
            fig2.update_layout(
                plot_bgcolor="#161b22", paper_bgcolor="#0d1117",
                font_color="#e6edf3", margin=dict(l=20, r=20, t=40, b=20),
            )
            st.plotly_chart(fig2, use_container_width=True, key="odi_wkt_scatter")
        st.dataframe(df, use_container_width=True, hide_index=True)
 
    # ── TAB 4 : Run scorers ───────────────────────────────────────────
    with tabs[2]:
        # st.markdown("### Highest Run-Scorers in ODI Internationals")
        # n = st.slider("Top N batsmen", 5, 20, 10, key="odi_run_n")
        df, fig = analysis_run_scorers(odi_batting, players_df=odi_players, top_n=12)

        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.bar(
                df, x="runs", y="player_name", orientation="h",      # ← total_runs → runs
                color="runs", color_continuous_scale="Blues",
                labels={"runs": "Total Runs", "player_name": ""},
                title="Total Runs", text="runs",
            )
            fig1.update_traces(textposition="outside")
            fig1.update_layout(
                yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False,
                plot_bgcolor="#161b22", paper_bgcolor="#0d1117", font_color="#e6edf3",
                margin=dict(l=20, r=20, t=40, b=20),
            )
            st.plotly_chart(fig1, use_container_width=True, key="odi_runs_chart")

        with c2:
            if "strike_rate" in df.columns:                           # ← safe check
                fig2 = px.bar(
                    df, x="strike_rate", y="player_name", orientation="h",   # ← avg_sr → strike_rate
                    color="strike_rate", color_continuous_scale="Oranges",
                    labels={"strike_rate": "Strike Rate", "player_name": ""},
                    title="Strike Rate", text=df["strike_rate"].round(1),     # ← avg_sr → strike_rate
                )
                fig2.update_traces(textposition="outside")
                fig2.update_layout(
                    yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False,
                    plot_bgcolor="#161b22", paper_bgcolor="#0d1117", font_color="#e6edf3",
                    margin=dict(l=20, r=20, t=40, b=20),
                )
                st.plotly_chart(fig2, use_container_width=True, key="odi_sr_chart")

        st.dataframe(df, use_container_width=True, hide_index=True)
        
    # TAB : Sixes & Fours
    with tabs[3]:

        # ── By Player ─────────────────────────────────────────────
        # st.markdown("#### By Player")
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("##### 💥 Most Sixes")
            df_six, fig_six = analysis_most_sixes(odi_batting, players_df=odi_players, top_n=10)
            st.plotly_chart(fig_six, use_container_width=True, key="odi_six_player_chart")
            # st.dataframe(df_six, use_container_width=True, hide_index=True)
        with col_r:
            st.markdown("##### 4️⃣ Most Fours")
            df_four, fig_four = analysis_most_fours(odi_batting, players_df=odi_players, top_n=10)
            st.plotly_chart(fig_four, use_container_width=True, key="odi_four_player_chart")
            # st.dataframe(df_four, use_container_width=True, hide_index=True)

        st.divider()

        # ── By Team ───────────────────────────────────────────────
        # st.markdown("#### By Team")
        col_l2, col_r2 = st.columns(2)
        with col_l2:
            st.markdown("##### 💥 Sixes Per Team")
            df_tsix, fig_tsix = analysis_team_sixes(odi_batting, top_n=10)
            st.plotly_chart(fig_tsix, use_container_width=True, key="odi_six_team_chart")
            # st.dataframe(df_tsix, use_container_width=True, hide_index=True)
        with col_r2:
            st.markdown("##### 4️⃣ Fours Per Team")
            df_tfour, fig_tfour = analysis_team_fours(odi_batting, top_n=10)
            st.plotly_chart(fig_tfour, use_container_width=True, key="odi_four_team_chart")
            # st.dataframe(df_tfour, use_container_width=True, hide_index=True)
 
    # ── TAB 6 : Team rankings ─────────────────────────────────────────
    with tabs[4]:
        # st.markdown("### Most Successful Teams in ODIs")
        # n = st.slider("Top N teams", 5, 20, 10, key="odi_team_n")
        df, fig = analysis_successful_teams(odi_matches, top_n=12)
        st.plotly_chart(fig, use_container_width=True, key="odi_team_chart")
 
        if not df.empty and "win_pct" in df.columns:
            fig2 = px.treemap(
                df, path=["team"], values="wins",
                color="win_pct", color_continuous_scale="RdYlGn",
                hover_data=["matches_played", "wins", "win_pct"],
                title="Win % Treemap — ODI Teams",
            )
            fig2.update_layout(paper_bgcolor="#0d1117", font_color="#e6edf3")
            st.plotly_chart(fig2, use_container_width=True, key="odi_treemap")
 
        st.dataframe(df, use_container_width=True, hide_index=True)
        
# ═══════════════════════════════════════════════════════════════════════════════
# paste this INSIDE your  if page == "🎩 Test Rankings":  block in app.py
# ═══════════════════════════════════════════════════════════════════════════════
elif selected == "🎩 Test Analytics":
    from utils.test_loader   import load_all_test_data
    from utils.test_analysis import (
        get_matches_by_country, get_matches_by_venue,
        get_top_wicket_takers, get_top_run_scorers,
        get_team_rankings,
        get_dot_ball_by_bowler, get_dot_ball_by_team,
    )
    import plotly.express as px
    import plotly.graph_objects as go

    # ── Load data once ────────────────────────────────────────────────────────
    @st.cache_data
    def _load_test():
        return load_all_test_data()

    _td          = _load_test()
    matches_df   = _td["matches"]
    batting_df   = _td["batting"]
    bowling_df   = _td["bowling"]
    fow_df       = _td["fow"]
    partner_df   = _td["partnerships"]
    players_df   = _td["players"]
    
    st.markdown("""
        <style>
        .main-title {
            font-size: 40px;
            font-weight: 800;
            color: #00c853;
            text-align: center;
            margin-bottom: 0;
        }
    
        .sub-title {
            text-align: center;
            color: #bbbbbb;
            font-size: 18px;
            margin-top: -10px;
            margin-bottom: 25px;
        }
    
        .metric-card {
            background: linear-gradient(135deg, #1f1f1f, #2b2b2b);
            padding: 18px;
            border-radius: 18px;
            text-align: center;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.08);
        }
    
        .metric-value {
            font-size: 28px;
            font-weight: 700;
            color: white;
        }
    
        .metric-label {
            font-size: 15px;
            color: #cfcfcf;
        }
        </style>
        """, unsafe_allow_html=True)
    
        # ================= TITLE =================
    st.markdown(
            f"""
            <div class="main-title"> Test Match Analytics</div>
            <div class="sub-title">
            Test Cricket Matches • 1877 - 2024 • Complete Analysis
            </div>
            """,
            unsafe_allow_html=True
        )
   
    st.markdown("""
    <style>
    /* ── Center tablist ── */
    [data-testid="stTabs"] [role="tablist"] {
        justify-content: center !important;
        gap: 6px !important;
        border-bottom: none !important;
        flex-wrap: wrap !important;
    }
    
    /* ── All tabs base ── */
    [data-testid="stTabs"] [role="tab"] {
        font-size: 12px !important;
        font-weight: 500 !important;
        padding: 8px 14px !important;
        border-radius: 10px !important;
        color: #aaaaaa !important;
        background: #2a2a2a !important;
        border: none !important;
        transition: all 0.2s ease !important;
        white-space: nowrap !important;
    }
    
    /* ── Hover ── */
    [data-testid="stTabs"] [role="tab"]:hover {
        background: #333333 !important;
        color: #ffffff !important;
    }
    
    /* ── Active tab — filled orange ── */
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        background: #ff8c00 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-bottom: none !important;
        box-shadow: 0 2px 12px rgba(255, 140, 0, 0.3) !important;
    }
    
    /* ── Remove default underline indicator ── */
    [data-testid="stTabs"] [role="tab"][aria-selected="true"]::before,
    [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        display: none !important;
        background: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)
    tabs = st.tabs([
        "Countries & Venues",
        "Wicket Takers",
        "Run Scorers",
        "Team Rankings",
        "Dot Balls",
    ])

    # ── Tab 1: Countries & Venues ─────────────────────────────────────────────
    with tabs[0]:
        # st.markdown("### 🌍 Countries & Venues")

        country_df = get_matches_by_country(matches_df)
        venue_df   = get_matches_by_venue(matches_df)

        # --- Country Chart ---
        if not country_df.empty:
            top_countries = country_df.head(15)
            fig_country = px.bar(
                top_countries,
                x="Matches", y="Country",
                orientation="h",
                title="Top 15 Countries by Matches Hosted",
                color="Matches",
                color_continuous_scale="Blues",
                text="Matches",
            )
            fig_country.update_traces(textposition="outside")
            fig_country.update_layout(
                yaxis=dict(autorange="reversed"),
                coloraxis_showscale=False,
                height=500,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_country, use_container_width=True)

        # --- Venue Chart (Top 20) ---
        if not venue_df.empty:
            top_venues = venue_df.head(20)
            fig_venue = px.bar(
                top_venues,
                x="Matches", y="Venue",
                orientation="h",
                title="Top 20 Venues by Matches Hosted",
                color="Matches",
                color_continuous_scale="Oranges",
                text="Matches",
            )
            fig_venue.update_traces(textposition="outside")
            fig_venue.update_layout(
                yaxis=dict(autorange="reversed"),
                coloraxis_showscale=False,
                height=600,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_venue, use_container_width=True)
            
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Matches per Country**")
            st.dataframe(country_df, use_container_width=True, hide_index=True)
        with col2:
            st.markdown("**Matches per Venue**")
            st.dataframe(venue_df, use_container_width=True, hide_index=True)

    # ── Tab 2: Wicket Takers ──────────────────────────────────────────────────
    with tabs[1]:
        # st.markdown("### Top Wicket Takers")
        teams_bowl = ["All"] + sorted(bowling_df["team"].dropna().unique().tolist()) if not bowling_df.empty else ["All"]
        c1, c2, c3 = st.columns(3)
        t_filter   = c1.selectbox("Team",    teams_bowl,             key="wkt_team")
        min_wkts   = c2.number_input("Min Wickets", 0, value=50,     key="min_wkts")
        inn_filter = c3.selectbox("Innings", ["All","1","2","3","4"], key="wkt_inn")

        df_wkt = get_top_wicket_takers(bowling_df, players_df,
                                       team=t_filter, innings=inn_filter,
                                       min_wickets=int(min_wkts))

        if not df_wkt.empty:
            name_col = "player_name" if "player_name" in df_wkt.columns else "Player ID"
            top_wkt  = df_wkt.head(20)

            # Bar: Wickets
            fig_wkt = px.bar(
                top_wkt,
                x=name_col, y="Wickets",
                title="Top 20 Wicket Takers",
                color="Wickets",
                color_continuous_scale="Reds",
                text="Wickets",
            )
            fig_wkt.update_traces(textposition="outside")
            fig_wkt.update_layout(
                xaxis_tickangle=-45,
                coloraxis_showscale=False,
                height=500,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_wkt, use_container_width=True)

            # Scatter: Average vs Strike Rate
            fig_scatter = px.scatter(
                df_wkt.head(50),
                x="Average", y="Strike Rate",
                size="Wickets",
                color="Wickets",
                hover_name=name_col,
                hover_data=["Wickets", "Economy"],
                title="Bowling Average vs Strike Rate (Top 50, bubble = wickets)",
                color_continuous_scale="Plasma",
            )
            fig_scatter.update_layout(
                height=500,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        st.dataframe(df_wkt, use_container_width=True, hide_index=True)

    # ── Tab 3: Run Scorers ────────────────────────────────────────────────────
    with tabs[2]:
        # st.markdown("###  Top Run Scorers")
        teams_bat = ["All"] + sorted(batting_df["team"].dropna().unique().tolist()) if not batting_df.empty else ["All"]
        c1, c2, c3 = st.columns(3)
        t_filter_b   = c1.selectbox("Team",    teams_bat,              key="run_team")
        min_runs     = c2.number_input("Min Runs", 0, value=1000,      key="min_runs")
        inn_filter_b = c3.selectbox("Innings", ["All","1","2","3","4"], key="run_inn")

        df_bat = get_top_run_scorers(batting_df, players_df,
                                     team=t_filter_b, innings=inn_filter_b,
                                     min_runs=int(min_runs))

        if not df_bat.empty:
            name_col = "player_name" if "player_name" in df_bat.columns else "Player ID"
            top_bat  = df_bat.head(20)

            # Bar: Runs
            fig_runs = px.bar(
                top_bat,
                x=name_col, y="Runs",
                title="Top 20 Run Scorers",
                color="Runs",
                color_continuous_scale="Greens",
                text="Runs",
            )
            fig_runs.update_traces(textposition="outside")
            fig_runs.update_layout(
                xaxis_tickangle=-45,
                coloraxis_showscale=False,
                height=500,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_runs, use_container_width=True)

            # 100s vs 50s grouped bar
            fig_miles = go.Figure()
            fig_miles.add_trace(go.Bar(
                name="100s",
                x=top_bat[name_col],
                y=top_bat["100s"],
                marker_color="#f59e0b",
                text=top_bat["100s"],
                textposition="outside",
            ))
            fig_miles.add_trace(go.Bar(
                name="50s",
                x=top_bat[name_col],
                y=top_bat["50s"],
                marker_color="#6366f1",
                text=top_bat["50s"],
                textposition="outside",
            ))
            fig_miles.update_layout(
                barmode="group",
                title="Centuries (100s) vs Half-Centuries (50s) — Top 20",
                xaxis_tickangle=-45,
                height=500,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_miles, use_container_width=True)

            # Scatter: Average vs Strike Rate
            fig_bat_scatter = px.scatter(
                df_bat.head(50),
                x="Average", y="Strike Rate",
                size="Runs",
                color="100s",
                hover_name=name_col,
                hover_data=["Runs", "Innings", "HS"],
                title="Batting Average vs Strike Rate (Top 50, bubble = runs)",
                color_continuous_scale="Viridis",
            )
            fig_bat_scatter.update_layout(
                height=500,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_bat_scatter, use_container_width=True)

        st.dataframe(df_bat, use_container_width=True, hide_index=True)

    # ── Tab 4: Team Rankings ──────────────────────────────────────────────────
    with tabs[3]:
        # st.markdown("### Team Rankings")
        sort_by  = st.selectbox("Sort by", ["Win %", "Wins", "Matches"], key="team_sort")
        df_teams = get_team_rankings(matches_df, sort_by=sort_by)

        if df_teams.empty:
            st.info("No match data available.")
        else:
            # Stacked bar: Wins / Losses / Draws
            fig_team = go.Figure()
            fig_team.add_trace(go.Bar(
                name="Wins",
                x=df_teams["Team"],
                y=df_teams["Wins"],
                marker_color="#22c55e",
            ))
            fig_team.add_trace(go.Bar(
                name="Losses",
                x=df_teams["Team"],
                y=df_teams["Losses"],
                marker_color="#ef4444",
            ))
            fig_team.add_trace(go.Bar(
                name="Draws",
                x=df_teams["Team"],
                y=df_teams["Draws"],
                marker_color="#94a3b8",
            ))
            fig_team.update_layout(
                barmode="stack",
                title="Team Records — Wins / Losses / Draws",
                xaxis_tickangle=-45,
                height=500,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_team, use_container_width=True)

            # Win % bar
            fig_winpct = px.bar(
                df_teams.sort_values("Win %", ascending=False),
                x="Team", y="Win %",
                title="Win Percentage by Team",
                color="Win %",
                color_continuous_scale="RdYlGn",
                text="Win %",
            )
            fig_winpct.update_traces(texttemplate="%{text}%", textposition="outside")
            fig_winpct.update_layout(
                xaxis_tickangle=-45,
                coloraxis_showscale=False,
                height=500,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_winpct, use_container_width=True)

            st.dataframe(df_teams, use_container_width=True, hide_index=True)

    # ── Tab 5: Dot Balls ──────────────────────────────────────────────────────
    with tabs[4]:
        # st.markdown("### Dot Ball Analysis")
        teams_dot = ["All"] + sorted(bowling_df["team"].dropna().unique().tolist()) if not bowling_df.empty else ["All"]
        c1, c2, c3 = st.columns(3)
        dot_view = c1.selectbox("View by", ["Bowler", "Team"], key="dot_view")
        dot_team = c2.selectbox("Team",    teams_dot,          key="dot_team")
        dot_min  = c3.number_input("Min Balls", 0, value=60,   key="dot_min")

        if dot_view == "Bowler":
            df_dot = get_dot_ball_by_bowler(bowling_df, players_df,
                                            team=dot_team, min_balls=int(dot_min))
        else:
            df_dot = get_dot_ball_by_team(bowling_df, min_balls=int(dot_min))

        if df_dot.empty:
            st.info("No bowling data available.")
        else:
            m1, m2, m3 = st.columns(3)
            label = "Total Bowlers" if dot_view == "Bowler" else "Total Teams"
            m1.metric(label, len(df_dot))
            m2.metric("Avg Dot Ball %", f"{df_dot['Dot Ball %'].mean():.1f}%")
            m3.metric("Highest Dot Ball %", f"{df_dot['Dot Ball %'].max():.1f}%")

            name_col = "player_name" if "player_name" in df_dot.columns else (
                "Team" if dot_view == "Team" else "Player ID"
            )
            top_dot = df_dot.head(20)

            # Bar: Dot Ball %
            fig_dot = px.bar(
                top_dot,
                x=name_col, y="Dot Ball %",
                title=f"Top 20 by Dot Ball % ({'Bowler' if dot_view == 'Bowler' else 'Team'})",
                color="Dot Ball %",
                color_continuous_scale="Greys",
                text=top_dot["Dot Ball %"].apply(lambda x: f"{x:.1f}%"),
            )
            fig_dot.update_traces(textposition="outside")
            fig_dot.update_layout(
                xaxis_tickangle=-45,
                coloraxis_showscale=False,
                height=500,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_dot, use_container_width=True)

            # Scatter: Dot Ball % vs Economy
            fig_dot_sc = px.scatter(
                df_dot.head(50),
                x="Dot Ball %", y="Economy",
                size="Balls",
                color="Wickets",
                hover_name=name_col,
                hover_data=["Dots", "Balls"],
                title="Dot Ball % vs Economy (Top 50, bubble = balls bowled)",
                color_continuous_scale="Blues",
            )
            fig_dot_sc.update_layout(
                height=500,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_dot_sc, use_container_width=True)

            st.dataframe(df_dot, use_container_width=True, hide_index=True)
            
if __name__ == "__main__":
    print("This file contains the T20 Rankings tab code snippet.")
    print("Copy the string T20_TAB_CODE into your app.py as instructed.")
    
    
    
    