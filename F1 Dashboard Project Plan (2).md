
# Interactive F1 Dashboard — Final Plan (Beginner-Friendly, Vercel-Ready, Monorepo)

> **This is the single source of truth** for building and deploying your F1 dashboard.  
> Written for someone **new to everything**. We use **one GitHub repo (monorepo)**.  
> **Nothing is marked as done** — all checkboxes are intentionally unchecked.  
> FastF1 docs link for any AI helper: <https://theoehrly.github.io/Fast-F1/>

---

## 0) Decisions We Agreed On (TL;DR)

- **Repo:** Use **one GitHub repo (monorepo)** with `web/` (Next.js) and `api/` (FastAPI).
- **Frontend host:** **Vercel (Hobby)** for the Next.js site.
- **Backend host:** **Render (Free)** to start (expect cold starts & no persistent disk). Upgrade later if needed.
- **Database:** **Supabase (Free)** Postgres for persistence (avoid Render Free Postgres which expires).
- **Scheduler:** Use **GitHub Actions cron** (free for public repos) instead of Vercel Cron for frequent jobs.
- **Weather:** Start with **Open-Meteo** (no API key), add **Meteostat** for historical if needed.
- **FastF1:** Use Python FastF1 with on-disk cache (ephemeral on Render Free; persist later if upgrading).
- **Results Archive:** Include a full **year → race** browser with finish order, gaps, tyres, pit stops, weather.
- **Predictor:** Backend ML (e.g., XGBoost/LightGBM) + **slider overlay** to adjust probabilities server-side.
- **Provide docs:** Share the FastF1 docs link with any AI or collaborator.

---

## 1) What We’re Building (Scope)

- [ ] **Map page**: interactive world map of circuits (filter by year, click to open race details).
- [ ] **Season pages**: list races for any season with dates and status.
- [ ] **Race pages**: Overview | Results | Laps | Strategy | Weather tabs.
- [ ] **Results Archive**: browse historical results by year → race; export CSV/PNG.
- [ ] **Predictor**: sliders (Track Suitability, Clean Air Pace, Quali Importance, Team Form, Weather Impact, Chaos) with live predicted order + explanations.
- [ ] **Driver/Team pages**: trends, best/worst circuits, quali vs race deltas.
- [ ] **Weather-aware** modeling (live + historical) with configurable heuristics/weights.
- [ ] **API** with OpenAPI docs; unit tests + backtests for the model.
- [ ] **DB** persistence for schedules, results, weather, predictions.

---

## 2) Tech Stack (What & Why)

### Frontend (Vercel)
- **Next.js (TypeScript)** — Vercel-native framework for React.
- **Tailwind CSS** — fast, utility-first styling.
- **shadcn/ui** — accessible, ready-made components.
- **Leaflet** — map rendering (circuits).
- **Recharts** (or ECharts) — charts for laps, gaps, stints.
- **TanStack Query** — data fetching & caching in the browser.

### Backend (Render)
- **FastAPI (Python)** — simple, fast API server.
- **FastF1** — F1 data: schedule, laps, sectors, telemetry, tyres/stints, pit stops, session results.
- **SQLAlchemy** — DB ORM.
- **httpx** — HTTP client for weather APIs.
- **XGBoost/LightGBM** — ML for predictions (start with one).

### Database & Storage
- **Supabase Postgres (Free)** — persistent database.
- **Supabase Storage** (optional) — store model artifacts or cached parquet files.

### Weather
- **Open-Meteo** (no key) — forecast & current.
- **Meteostat** — historical (API quota is small; bulk data also available).

### Dev Tooling
- **Node 20+** & **pnpm** for frontend.
- **Python 3.11+** with **uv** or **venv + pip** for backend.
- **GitHub** for code + Actions cron.

---

## 3) Monorepo Layout (One Repo)

```
f1-dashboard/
├── web/                # Next.js frontend (Vercel)
│   ├── app/            # routes: map, season, race, predict, results, driver, team
│   ├── components/     # MapView, ResultTable, LapChart, WeightSliders, WeatherWidget...
│   └── lib/            # API client, utilities
├── api/                # FastAPI backend (Render)
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/    # seasons.py, races.py, weather.py, predict.py, results.py, cron.py
│   │   ├── services/   # fastf1_service.py, weather_service.py, prediction_service.py, ingest_service.py
│   │   ├── models/     # SQLAlchemy models
│   │   └── schemas/    # Pydantic
│   └── requirements.txt
├── data/               # circuits.csv, qualifying_2025.csv (optional seed)
├── config/             # weather_effects.json (tunable heuristics)
└── .github/workflows/  # GitHub Actions cron (keepalive/refresh/retrain)
```

**One repo** powers two deploys:
- Vercel deploys from `web/` (Root Directory setting).
- Render deploys from `api/` (Root Directory setting).

---

## 4) Deployment Matrix (Who Deploys What)

| Piece | Host | How to point to subfolder | Notes |
|---|---|---|---|
| Frontend (`web/`) | **Vercel (Hobby)** | Project → Settings → **Root Directory = `web`** | Add env vars and deploy via GitHub. |
| Backend (`api/`) | **Render (Free)** | New → Web Service → **Root Directory = `api`** | Build: `pip install -r requirements.txt` · Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| DB | **Supabase (Free)** | N/A | Create project, run schema SQL, copy connection string to backend `DB_URL`. |
| Cron | **GitHub Actions** | `.github/workflows/*.yml` | Calls backend endpoints with a token to warm caches/backfill. |

---

## 5) Environment Variables (Where to Set Them)

### Vercel (Frontend)
```
NEXT_PUBLIC_API_BASE = https://<your-render-app>.onrender.com
NEXT_PUBLIC_MAP_TILE_URL = https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
```

### Render (Backend)
```
DB_URL = postgresql+psycopg://<supabase-connection-string>
FASTF1_CACHE_DIR = .fastf1_cache
WEATHER_PROVIDER = open-meteo
SUPABASE_URL = https://<your-supabase-ref>.supabase.co
SUPABASE_SERVICE_ROLE = <service-role-key>   # never expose to frontend
CRON_TOKEN = <long-random-string>           # to protect /cron endpoints
CORS_ORIGINS = https://<your-vercel-domain> # or comma-separated list
```

### GitHub (Actions)
- **Repository Variable:** `API_BASE = https://<your-render-app>.onrender.com`
- **Repository Secret:** `CRON_TOKEN = <same as backend>`

---

## 6) GitHub Actions Cron (Recommended)

**Why:** Free for public repos, simple YAML, good logs, and frequent schedules.

Place these in `.github/workflows/`:

**A) Keep backend warm (~every 14 min)**
```yaml
name: Keep Backend Warm
on:
  schedule: [{ cron: "*/14 * * * *" }]
  workflow_dispatch: {}
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping /cron/warmup
        env:
          API: ${{ vars.API_BASE }}
          TOKEN: ${{ secrets.CRON_TOKEN }}
        run: curl -fsS -H "Authorization: Bearer $TOKEN" "$API/cron/warmup" || true
```

**B) Nightly data refresh**
```yaml
name: Nightly Data Refresh
on:
  schedule: [{ cron: "0 2 * * *" }]
  workflow_dispatch: {}
jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - name: Backfill seasons
        env:
          API: ${{ vars.API_BASE }}
          TOKEN: ${{ secrets.CRON_TOKEN }}
        run: |
          curl -fsS -X POST             -H "Authorization: Bearer $TOKEN"             -H "Content-Type: application/json"             -d '{"years":[2020,2021,2022,2023,2024,2025]}'             "$API/cron/ingest"
```

**C) Weekly model retrain**
```yaml
name: Retrain Model
on:
  schedule: [{ cron: "0 3 * * MON" }]
  workflow_dispatch: {}
jobs:
  retrain:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger retrain
        env:
          API: ${{ vars.API_BASE }}
          TOKEN: ${{ secrets.CRON_TOKEN }}
        run: curl -fsS -X POST -H "Authorization: Bearer $TOKEN" "$API/cron/retrain"
```

---

## 7) Backend `/cron/*` Endpoints (Spec)

- `GET /cron/warmup`
  - **Auth:** `Authorization: Bearer <CRON_TOKEN>`
  - **Action:** Touch recent sessions, pre-load FastF1 subset, refresh simple caches. Return quickly.

- `POST /cron/ingest`
  - **Auth:** Bearer token.
  - **Body (example):**
    ```json
    { "years": [2020, 2021, 2022, 2023, 2024, 2025] }
    ```
  - **Action:** Pull season schedule + results + minimal weather windows into DB.

- `POST /cron/retrain`
  - **Auth:** Bearer token.
  - **Action:** Queue or kick off background model training (return 202 Accepted quickly; do the heavy work async if possible).

---

## 8) API Contract (v1)

- `GET /seasons/{year}/races` → list races with date & circuit meta.
- `GET /races/{year}/{round}` → overview + results if available.
- `GET /races/{year}/{round}/laps?session=R|Q|FP1` → lap data.
- `GET /races/{year}/{round}/weather` → normalized weather series (cached).
- `GET /results/{year}` and `GET /results/{year}/{round}` → **Results Archive** (full classification).
- `POST /predictions/{year}/{round}` → ranked order with probabilities & explanations.
  ```json
  {
    "weights": {
      "track_suitability": 0.85,
      "clean_air_pace": 0.90,
      "qualifying_importance": 0.85,
      "team_form": 0.68,
      "weather_impact": 0.45,
      "chaos_mode": true
    }
  }
  ```

---

## 9) Database Schema (Minimal)

```sql
CREATE TABLE circuits (
  circuit_key TEXT PRIMARY KEY,
  name TEXT, locality TEXT, country TEXT,
  latitude REAL, longitude REAL, type TEXT,
  distance_km REAL, laps INTEGER, drs_zones INTEGER, altitude_m REAL
);

CREATE TABLE races (
  id INTEGER PRIMARY KEY,
  year INTEGER, round INTEGER, circuit_key TEXT,
  grand_prix TEXT, race_date DATE, session_start TIMESTAMP,
  FOREIGN KEY (circuit_key) REFERENCES circuits(circuit_key)
);

CREATE TABLE results (
  race_id INTEGER, driver_code TEXT, team TEXT,
  grid INTEGER, finish_pos INTEGER, status TEXT,
  pit_stops INTEGER, total_time_ms INTEGER, fastest_lap_ms INTEGER,
  tyre_stints TEXT,
  PRIMARY KEY (race_id, driver_code)
);

CREATE TABLE qualifying (
  race_id INTEGER, driver_code TEXT, team TEXT,
  q1_ms INTEGER, q2_ms INTEGER, q3_ms INTEGER, grid_penalty TEXT,
  quali_pos INTEGER,
  PRIMARY KEY (race_id, driver_code)
);

CREATE TABLE weather (
  race_id INTEGER, ts TIMESTAMP, temp_c REAL, wind_kph REAL, precip_prob REAL,
  precip_mm REAL, cloud_pct INTEGER, humidity_pct INTEGER, pressure_hpa REAL,
  track_wet BOOLEAN, PRIMARY KEY (race_id, ts)
);

CREATE TABLE predictions (
  race_id INTEGER, model_version TEXT, run_ts TIMESTAMP,
  params_json JSON, predictions_json JSON, metrics_json JSON
);
```

---

## 10) Predictor & Features (Summary)

**Targets**
- Winner probability per driver; Top-3 probability; full ranking (optional).

**Base features**
- Track Suitability (driver+team on similar circuits).
- Clean-Air Race Pace (median clean laps; EWMA over recent races).
- Qualifying Importance (grid pos., overtaking difficulty at circuit).
- Team Form (constructor EWMA; pit-stop reliability).
- Weather Impact (rain prob., wind, temp; driver wet-weather delta).
- Chaos (SC/VSC frequency, DNF rates → variance).

**Model**
- Start with **XGBoost/LightGBM** for win/top-3.
- Optionally **LambdaMART** for learning-to-rank.
- **Explainability:** SHAP or permutation importance.

**Overlay (sliders)**
```
score(d) = p_model(d)
         + α1*t*Z_track(d) + α2*p*Z_pace(d) + α3*q*Z_quali(d)
         + α4*f*Z_team(d) + α5*w*Z_weather(d)
if chaos: add noise ~ N(0, σ_chaos); renormalize to probabilities
```

---

## 11) Minimal FastF1 Patterns (for implementers and AI)

```python
import fastf1
fastf1.Cache.enable_cache(".fastf1_cache")

# Load a session
session = fastf1.get_session(2024, "Monaco Grand Prix", "R")  # FP1/FP2/FP3/Q/R
session.load(laps=True, telemetry=False)

# Laps & results
laps = session.laps               # DataFrame: lap times, sectors, driver, etc.
results = session.results         # race classification

# Telemetry for fastest lap of a driver
lap = laps.pick_driver("VER").pick_fastest()
tel = lap.get_car_data().add_distance()

# Pit stops & tyres
stops = session.get_pitstops()
```

---

## 12) Setup Steps (Copy/Paste)

**Repo & folders**
```bash
mkdir f1-dashboard && cd f1-dashboard
mkdir web api
git init && git add . && git commit -m "chore: init monorepo"
git branch -M main
git remote add origin <your-github-url>
git push -u origin main
```

**Frontend scaffold**
```bash
cd web
pnpm create next-app@latest . --ts --eslint --app --src-dir
pnpm i tailwindcss @tanstack/react-query leaflet recharts
npx tailwindcss init -p
git add . && git commit -m "feat(web): scaffold" && git push
```

**Backend scaffold**
```bash
cd ../api
python -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn fastf1 httpx sqlalchemy pydantic xgboost python-dotenv
echo "fastapi
uvicorn
fastf1
httpx
sqlalchemy
pydantic
xgboost
python-dotenv" > requirements.txt
# create app/main.py and basic routers per spec
git add . && git commit -m "feat(api): scaffold" && git push
```

**Deploy**
- **Vercel** → import repo → **Root Directory = `web`** → set env vars → deploy.
- **Render** → New Web Service from repo → **Root Directory = `api`** → build & start commands → env vars → deploy.
- **Supabase** → create project → run SQL schema → copy connection string → put into Render `DB_URL`.

**GitHub Actions (cron)**
- Add workflows from Section 6 into `.github/workflows/` and set `API_BASE` (Variable) + `CRON_TOKEN` (Secret).

---

## 13) Operational Notes (Free Tier Realities)

- **Render Free**: service **sleeps after ~15 minutes** idle; first hit can be slow. No persistent disk, so FastF1 cache resets on redeploys; acceptable for testing. Upgrade later to attach disk and keep it warm.
- **Supabase Free**: good for getting started (DB caps exist). Projects can pause after long inactivity—open the project periodically.
- **GitHub Actions**: cron runs in UTC and may be a few minutes late; fine for warmups/backfills.
- **Time zones**: store all timestamps as UTC; convert to local in the UI.
- **Legal/Ethical**: follow provider terms; add disclaimer (“not betting advice”).

---

## 14) Checklists (Intentionally All Unchecked)

**Core features**
- [ ] Map of circuits
- [ ] Season pages + schedule
- [ ] Race pages (Overview, Results, Laps, Strategy, Weather)
- [ ] Results Archive (year → race)
- [ ] Predictor (sliders + live ranking)
- [ ] Weather integration and effects

**Data & modeling**
- [ ] Historical ingest to DB
- [ ] Feature builder
- [ ] Train baseline model
- [ ] Evaluate (Brier/log loss, rank correlation)
- [ ] Explainability

**Ops**
- [ ] Vercel deploy (frontend)
- [ ] Render deploy (backend)
- [ ] Supabase initialized
- [ ] GitHub cron workflows active
- [ ] Error monitoring & logging

**Docs**
- [ ] API reference (OpenAPI)
- [ ] How to add a new season
- [ ] Troubleshooting (FastF1 cache, timeouts, weather, CORS)

---

This plan reflects **everything we discussed and decided**. Keep this file in the repo root so devs (and AI tools) follow a single, consistent blueprint.
