from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

from .routers import seasons, races, weather, predict, results, cron

load_dotenv()

app = FastAPI(
    title="F1 Prediction Dashboard API",
    description="API for F1 race predictions, results, and analytics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(seasons.router, prefix="/seasons", tags=["seasons"])
app.include_router(races.router, prefix="/races", tags=["races"])
app.include_router(weather.router, prefix="/weather", tags=["weather"])
app.include_router(predict.router, prefix="/predictions", tags=["predictions"])
app.include_router(results.router, prefix="/results", tags=["results"])
app.include_router(cron.router, prefix="/cron", tags=["cron"])

@app.get("/")
async def root():
    return {"message": "F1 Prediction Dashboard API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}