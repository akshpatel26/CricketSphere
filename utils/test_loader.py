import pandas as pd
import os

# ── Robust path: works whether called from app.py, utils/, or notebook ────────
_THIS_FILE = os.path.abspath(__file__)          # .../utils/test_loader.py
_UTILS_DIR = os.path.dirname(_THIS_FILE)        # .../utils/
_ROOT_DIR  = os.path.dirname(_UTILS_DIR)        # .../IPL Data Analytics/
DATA_DIR   = os.path.join(_ROOT_DIR, "data")    # .../IPL Data Analytics/data/

def _debug():
    """Call this once to verify paths — remove after fix."""
    print(f"[test_loader] ROOT : {_ROOT_DIR}")
    print(f"[test_loader] DATA : {DATA_DIR}")
    print(f"[test_loader] DATA exists: {os.path.exists(DATA_DIR)}")
    if os.path.exists(DATA_DIR):
        files = [f for f in os.listdir(DATA_DIR) if "test" in f.lower()]
        print(f"[test_loader] Test files found: {files}")

def _read(filename: str) -> pd.DataFrame:
    """Safe CSV reader with clear error messages."""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"[test_loader] ❌ NOT FOUND: {path}")
        # Try case-insensitive match
        if os.path.exists(DATA_DIR):
            all_files = os.listdir(DATA_DIR)
            match = next((f for f in all_files if f.lower() == filename.lower()), None)
            if match:
                path = os.path.join(DATA_DIR, match)
                print(f"[test_loader] ✅ Found via case-fix: {match}")
            else:
                print(f"[test_loader] Available files: {all_files}")
                return pd.DataFrame()
        else:
            return pd.DataFrame()
    try:
        df = pd.read_csv(path)
        df.columns = df.columns.str.strip()
        print(f"[test_loader] ✅ Loaded {filename}: {df.shape}")
        return df
    except Exception as e:
        print(f"[test_loader] ❌ Error reading {filename}: {e}")
        return pd.DataFrame()


def load_test_matches() -> pd.DataFrame:
    return _read("test_Matches_Data.csv")


def load_test_batting() -> pd.DataFrame:
    df = _read("test_Batting_Card.csv")
    if df.empty:
        return df
    for col in ["runs", "balls", "fours", "sixes", "strikeRate"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if "isOut" in df.columns:
        df["isOut"] = df["isOut"].map(
            {"TRUE": True, "FALSE": False, True: True, False: False}
        ).fillna(False).astype(bool)
    return df


def load_test_bowling() -> pd.DataFrame:
    df = _read("test_Bowling_Card.csv")
    if df.empty:
        return df
    for col in ["overs", "balls", "maidens", "conceded", "wickets",
                "economy", "dots", "fours", "sixes", "wides", "noballs"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def load_test_fow() -> pd.DataFrame:
    return _read("test_Fow_Card.csv")


def load_test_partnerships() -> pd.DataFrame:
    df = _read("test_Partnership_Card.csv")
    if df.empty:
        return df
    for col in ["player1 runs", "player2 runs", "player1 balls",
                "player2 balls", "partnership runs", "partnership balls"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def load_test_players() -> pd.DataFrame:
    return _read("players_info_test.csv")


def load_all_test_data() -> dict:
    _debug()   # prints path info — remove this line after confirming it works
    return {
        "matches":      load_test_matches(),
        "batting":      load_test_batting(),
        "bowling":      load_test_bowling(),
        "fow":          load_test_fow(),
        "partnerships": load_test_partnerships(),
        "players":      load_test_players(),
    }