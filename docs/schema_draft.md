# Data Schema (DRAFT) — nba-analytics-app
Status: DRAFT (will change). Goal is to document current assumptions & column meanings.

## Conventions
- All timestamps stored as UTC in DB (source may be EST); display layer converts as needed.
- Primary keys:
  - game_id: int/str from source
  - team_id: NBA teamId (e.g., 1610612746)
  - player_id: personId
- Missing values:
  - Empty string in raw CSV becomes NULL in DB.
- All “*_id” columns are treated as strings in the pipeline to avoid integer overflow / formatting issues.

---

## Entities

### games (source: `data/raw/games.csv`)
**Grain:** 1 row per game.

| column | type | nullable | example | notes |
|---|---:|---:|---|---|
| gameId | string | no | 22500827 | PK |
| gameDateTimeEst | datetime | no | 2026-02-22 21:00:00 | source timezone; convert to UTC on ingest |
| hometeamId | string | no | 1610612746 | FK → teams.team_id |
| awayteamId | string | no | 1610612753 | FK → teams.team_id |
| homeScore | int | yes | 109 | NULL if not played |
| awayScore | int | yes | 111 | NULL if not played |
| winner | string | yes | 1610612753 | team_id of winner |
| gameType | string | yes | Regular Season | |
| arenaId | string | yes | 1000137 | |
| officials | string | yes | "A, B, C" | raw string list |

**Derived fields (optional later):**
- season (e.g., 2025-26)
- is_played (homeScore IS NOT NULL AND awayScore IS NOT NULL)
- margin (homeScore - awayScore)

---

### players (source: `data/raw/players.csv`)
**Grain:** 1 row per player identity.

| column | type | nullable | example | notes |
|---|---:|---:|---|---|
| personId | string | no | 201939 | PK |
| firstName | string | yes | Stephen | |
| lastName | string | yes | Curry | |
| birthDate | date | yes | 1988-03-14 | |
| country | string | yes | USA | |
| heightInches | int | yes | 75 | |
| bodyWeightLbs | int | yes | 185 | |
| guard/forward/center | bool/int | yes | 1/0 | current file is inconsistent (0/1/false) → normalize |

**Normalization TODOs**
- Convert guard/forward/center to booleans consistently.
- Decide canonical “position” representation: enum vs 3 booleans.

---

### player_game_stats (planned; source: nba_api boxscore/traditional)
**Grain:** 1 row per player per game.

Keys:
- (game_id, player_id)

Core columns (initial):
- team_id
- minutes
- points, rebounds, assists, steals, blocks, turnovers
- fgm, fga, fg3m, fg3a, ftm, fta
- plus_minus

---

### team_game_stats (planned)
**Grain:** 1 row per team per game.

Keys:
- (game_id, team_id)

Core columns (initial):
- points
- off_rating/def_rating (or possessions + derived)
- pace proxy (possessions)
- rebounds, turnovers, etc.

---

## Data quality checks (informal for now)
- games: gameId unique, hometeamId != awayteamId
- played games: homeScore/awayScore are non-null and >= 0
- player_game_stats: minutes >= 0, points >= 0