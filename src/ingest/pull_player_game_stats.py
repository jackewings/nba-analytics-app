import pandas as pd
import ast
from pathlib import Path

def normalize_game_id(value: object) -> str:
    s = "" if value is None else str(value)
    if s.endswith(".0"):
        s = s[:-2]
    s = s.strip()
    return s.zfill(10) if s.isdigit() and len(s) < 10 else s

def extract_players_from_team_boxscore(team_boxscore_path: str, output_path: str, boxscore_type: str):
    # Ensure game_id never becomes an int/float (prevents dropping leading zeros)
    df = pd.read_csv(team_boxscore_path, dtype={"game_id": "string"})
    if "game_id" in df.columns:
        df["game_id"] = df["game_id"].map(normalize_game_id)

    rows = []
    for _, row in df.iterrows():
        game_id = row.get("game_id")
        team_id = row.get("teamId")
        team_name = row.get("teamName")
        try:
            players = ast.literal_eval(row.get("players", "[]"))
        except Exception:
            continue

        for player in players:
            player_row = {
                "game_id": game_id,
                "team_id": team_id,
                "team_name": team_name,
                "person_id": player.get("personId"),
                "first_name": player.get("firstName"),
                "family_name": player.get("familyName"),
                "position": player.get("position"),
                "comment": player.get("comment"),
                "jersey_num": player.get("jerseyNum"),
                "boxscore_type": boxscore_type,
            }
            stats = player.get("statistics", {})
            for k, v in stats.items():
                player_row[k] = v
            rows.append(player_row)

    player_df = pd.DataFrame(rows)
    player_df.to_csv(output_path, index=False)
    print(f"Saved {len(player_df)} player rows to {output_path}")

if __name__ == "__main__":
    data_dir = Path("data/raw/nba_api/2024_25")
    extract_players_from_team_boxscore(
        str(data_dir / "team_boxscore_traditional.csv"),
        str(data_dir / "player_boxscore_traditional.csv"),
        "traditional"
    )
    extract_players_from_team_boxscore(
        str(data_dir / "team_boxscore_advanced.csv"),
        str(data_dir / "player_boxscore_advanced.csv"),
        "advanced"
    )