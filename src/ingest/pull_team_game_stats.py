from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable

import pandas as pd
from nba_api.stats.endpoints import leaguegamelog, boxscoretraditionalv3, boxscoreadvancedv3

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "nba_api"


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def normalize_game_id(value: object) -> str:
    """
    Ensure NBA game_id is always a 10-character string with leading zeros.
    Examples:
      22400001 -> "0022400001"
      "0022400001" -> "0022400001"
    """
    s = "" if value is None else str(value)
    # handle accidental float-like strings: "22400001.0"
    if s.endswith(".0"):
        s = s[:-2]
    s = s.strip()
    return s.zfill(10) if s.isdigit() and len(s) < 10 else s


def pull_season_game_ids(season: str, season_type: str = "Regular Season") -> list[str]:
    """Pull all unique game IDs for the given season and season type."""
    gl = leaguegamelog.LeagueGameLog(season=season, season_type_all_star=season_type)
    df = gl.get_data_frames()[0]

    game_ids = (
        df["GAME_ID"]
        .dropna()
        .map(normalize_game_id)
        .drop_duplicates()
        .tolist()
    )
    return sorted(game_ids)


def _extract_teams(section: dict) -> list[dict]:
    """Extract team data from the boxscore section."""
    if not isinstance(section, dict):
        raise TypeError(f"Expected dict section, got {type(section)}")
    if "teams" in section and isinstance(section["teams"], list):
        return section["teams"]
    if "homeTeam" in section and "awayTeam" in section:
        return [section["homeTeam"], section["awayTeam"]]
    raise KeyError(f"Could not find team data. Section keys: {list(section.keys())}")


def pull_boxscore_team_traditional(game_id: str) -> pd.DataFrame:
    """Pull traditional team boxscore for a single game."""
    gid = normalize_game_id(game_id)
    bs = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=gid)
    d = bs.get_dict()
    section = d.get("boxScoreTraditional")
    if section is None:
        raise KeyError(f"Missing 'boxScoreTraditional'. Top-level keys: {list(d.keys())}")
    teams = _extract_teams(section)
    out = pd.json_normalize(teams)
    out["game_id"] = gid
    out["boxscore_type"] = "traditional"
    return out


def pull_boxscore_team_advanced(game_id: str) -> pd.DataFrame:
    """Pull advanced team boxscore for a single game."""
    gid = normalize_game_id(game_id)
    bs = boxscoreadvancedv3.BoxScoreAdvancedV3(game_id=gid)
    d = bs.get_dict()
    section = d.get("boxScoreAdvanced")
    if section is None:
        raise KeyError(f"Missing 'boxScoreAdvanced'. Top-level keys: {list(d.keys())}")
    teams = _extract_teams(section)
    out = pd.json_normalize(teams)
    out["game_id"] = gid
    out["boxscore_type"] = "advanced"
    return out


def _append_csv(path: Path, df: pd.DataFrame) -> None:
    """Append to CSV immediately; create with header if missing."""
    if df.empty:
        return
    if path.exists():
        df.to_csv(path, mode="a", header=False, index=False)
    else:
        df.to_csv(path, index=False)


def _done_game_ids(csv_path: Path) -> set[str]:
    """
    A game is considered done if we have BOTH teams for it:
    unique (game_id, teamId) pairs count to 2 teams per game.
    """
    if not csv_path.exists():
        return set()

    df = pd.read_csv(
        csv_path,
        dtype={"game_id": "string"},
        usecols=lambda c: c in {"game_id", "teamId"},
    )
    if df.empty:
        return set()

    df["game_id"] = df["game_id"].map(normalize_game_id)
    uniq = df.drop_duplicates(subset=["game_id", "teamId"])
    counts = uniq.groupby("game_id")["teamId"].nunique()
    return set(counts[counts >= 2].index)


def _with_retries(fn, *, retries: int = 4, base_sleep_s: float = 2.0):
    for attempt in range(retries + 1):
        try:
            return fn()
        except Exception:
            if attempt >= retries:
                raise
            time.sleep(base_sleep_s * (2 ** attempt))


def main(season: str = "2024-25", sleep_s: float = 1.0) -> None:
    out_dir = DATA_DIR / season.replace("-", "_")
    _ensure_dir(out_dir)

    trad_path = out_dir / "team_boxscore_traditional.csv"
    adv_path = out_dir / "team_boxscore_advanced.csv"

    game_ids = pull_season_game_ids(season=season)

    trad_done = _done_game_ids(trad_path)
    adv_done = _done_game_ids(adv_path)

    remaining = [gid for gid in game_ids if (gid not in trad_done) or (gid not in adv_done)]
    print(f"Season {season}: total_games={len(game_ids)} remaining={len(remaining)}")

    for idx, gid in enumerate(remaining, start=1):
        print(f"[{idx}/{len(remaining)}] game_id={gid}")

        if gid not in trad_done:
            try:
                trad_df = _with_retries(lambda: pull_boxscore_team_traditional(gid))
                _append_csv(trad_path, trad_df)
                # mark done if we got both teams
                if trad_df.get("teamId") is not None and trad_df["teamId"].nunique() >= 2:
                    trad_done.add(gid)
            except Exception as e:
                print(f"  traditional failed: {e}")
            time.sleep(sleep_s)

        if gid not in adv_done:
            try:
                adv_df = _with_retries(lambda: pull_boxscore_team_advanced(gid))
                _append_csv(adv_path, adv_df)
                if adv_df.get("teamId") is not None and adv_df["teamId"].nunique() >= 2:
                    adv_done.add(gid)
            except Exception as e:
                print(f"  advanced failed: {e}")
            time.sleep(sleep_s)

    print("Done.")


if __name__ == "__main__":
    main()

