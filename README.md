# F1 Prediction Dashboard

An interactive Formula 1 race predictions, analytics, and historical data visualization dashboard. Built with a modern tech stack and designed for deployment on Vercel (frontend) and Render (backend).

## 🏎️ Features

- **Interactive Circuit Map**: Explore F1 circuits around the world
- **Season Browser**: Browse races by season with dates and results
- **Results Archive**: Historical race results with detailed statistics  
- **Race Predictor**: AI-powered predictions with adjustable parameters
- **Analytics Dashboard**: Lap times, strategies, and performance analysis
- **Driver & Team Stats**: Comprehensive performance analysis

## 🏗️ Architecture

This is a **monorepo** setup with:
- `web/` - Next.js frontend (deployed to Vercel)
- `api/` - FastAPI backend (deployed to Render)
- `data/` - Seed data and circuit information
- `config/` - Weather effects and model configuration
- `.github/workflows/` - Automated cron jobs

## 🚀 Tech Stack

### Frontend
- **Next.js 15** with TypeScript
- **Tailwind CSS** for styling
- **shadcn/ui** for components
- **TanStack Query** for data fetching
- **Leaflet** for map visualization
- **Recharts** for data visualization

### Backend
- **FastAPI** with Python 3.11+
- **FastF1** for F1 data
- **SQLAlchemy** for database ORM
- **XGBoost** for ML predictions
- **httpx** for HTTP requests

### Database & Infrastructure
- **Supabase** (PostgreSQL) for production
- **SQLite** for local development
- **GitHub Actions** for automated tasks
- **Vercel** for frontend hosting
- **Render** for backend hosting

## 📦 Installation

### Prerequisites
- Node.js 20+
- Python 3.11+
- pnpm (recommended) or npm

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd f1-prediction-dashboard
```

### 2. Frontend Setup

```bash
cd web
npm install
cp .env.local.example .env.local
# Edit .env.local with your configuration
```

### 3. Backend Setup

```bash
cd ../api
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
```

## 🔧 Development

### Start Backend (Terminal 1)
```bash
cd api
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend (Terminal 2)
```bash
cd web
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 🚀 Deployment

### Vercel (Frontend)
1. Connect your GitHub repo to Vercel
2. Set **Root Directory** to `web`
3. Add environment variables:
   ```
   NEXT_PUBLIC_API_BASE=https://your-render-app.onrender.com
   NEXT_PUBLIC_MAP_TILE_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
   ```

### Render (Backend)
1. Create new Web Service from GitHub repo
2. Set **Root Directory** to `api`
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env.example`

### Supabase (Database)
1. Create new project
2. Run the SQL schema from the project plan
3. Copy connection string to `DB_URL` in Render

### GitHub Actions
1. Set repository variables:
   - `API_BASE`: Your Render backend URL
2. Set repository secrets:
   - `CRON_TOKEN`: Random string for cron endpoint security

## 📊 API Endpoints

- `GET /seasons/` - Available seasons
- `GET /seasons/{year}/races` - Races for a season
- `GET /races/{year}/{round}` - Race details
- `GET /races/{year}/{round}/laps` - Lap data
- `GET /weather/{year}/{round}` - Weather data
- `GET /results/{year}` - Season results
- `POST /predictions/{year}/{round}` - Race predictions
- `GET /health` - Health check

Full API documentation available at `/docs` when running the backend.

## 🔮 Current Status

✅ **Completed:**
- Monorepo structure setup
- Next.js frontend with TypeScript & Tailwind
- FastAPI backend with SQLAlchemy models
- Basic API endpoints structure
- GitHub Actions workflows
- Frontend-backend API client
- Seed data and configuration files

🚧 **In Progress:**
- Database setup and data ingestion
- FastF1 data integration
- ML prediction models
- Interactive map components
- Results archive functionality

⏳ **Planned:**
- Weather API integration
- Advanced analytics charts
- Driver/team performance pages
- Model training and evaluation
- Production deployment

## 📝 Environment Variables

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_MAP_TILE_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
```

### Backend (.env)
```bash
DB_URL=sqlite:///./f1_dashboard.db  # or PostgreSQL URL for production
FASTF1_CACHE_DIR=.fastf1_cache
WEATHER_PROVIDER=open-meteo
CRON_TOKEN=your-secure-token
CORS_ORIGINS=http://localhost:3000
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

For bugs and feature requests, please create an issue.

---

Built with ❤️ for Formula 1 fans and data enthusiasts.