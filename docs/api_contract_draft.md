# API Contract (DRAFT) — nba-analytics-app
Base URL: /api/v1
Status: DRAFT

## Health
GET /health
200 OK
{ "status": "ok" }

## Games (for browsing / selecting matchups)
GET /games?date=YYYY-MM-DD
200 OK
{
  "date": "2026-02-22",
  "games": [
    {
      "gameId": "22500827",
      "gameDateTimeEst": "2026-02-22 21:00:00",
      "home": { "teamId": "1610612746", "name": "Clippers", "city": "LA", "score": 109 },
      "away": { "teamId": "1610612753", "name": "Magic", "city": "Orlando", "score": 111 },
      "status": "final"
    }
  ]
}

GET /games/{gameId}
200 OK
{
  "gameId": "...",
  "homeTeamId": "...",
  "awayTeamId": "...",
  "homeScore": 109,
  "awayScore": 111,
  "winnerTeamId": "...",
  "gameType": "Regular Season"
}

## Teams / Players (optional for dropdowns/search)
GET /teams
200 OK
{ "teams": [ { "teamId": "...", "city": "...", "name": "..." } ] }

GET /players?query=steph
200 OK
{ "players": [ { "playerId": "201939", "firstName": "Stephen", "lastName": "Curry" } ] }

## Prediction (core)
POST /predict/game
Request:
{
  "homeTeamId": "1610612744",
  "awayTeamId": "1610612743",
  "gameDate": "2026-02-24",
  "context": {
    "includeInjuries": false,
    "useLastNGames": 10
  }
}

200 OK
{
  "homeTeamId": "1610612744",
  "awayTeamId": "1610612743",
  "predictedWinnerTeamId": "1610612744",
  "homeWinProbability": 0.62,
  "awayWinProbability": 0.38,
  "predictedScore": { "home": 116.4, "away": 111.2 },
  "model": {
    "name": "xgb_v3",
    "version": "2026-02-20",
    "featuresVersion": "fv_12"
  },
  "explanations": {
    "topFactors": [
      { "feature": "home_off_rating_last10", "impact": 0.08 },
      { "feature": "away_def_rating_last10", "impact": 0.05 }
    ]
  }
}

## (Optional) Predictions history
GET /predictions?date=YYYY-MM-DD