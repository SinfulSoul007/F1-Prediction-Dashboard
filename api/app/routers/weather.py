from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models.database import get_db
from ..models.models import Race, Weather

router = APIRouter()

@router.get("/{year}/{round}")
async def get_race_weather(year: int, round: int, db: Session = Depends(get_db)):
    """Get weather data for a specific race"""
    race = db.query(Race).filter(Race.year == year, Race.round == round).first()
    
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    
    weather_data = db.query(Weather).filter(Weather.race_id == race.id).order_by(Weather.ts).all()
    
    return {
        "race_id": race.id,
        "year": year,
        "round": round,
        "grand_prix": race.grand_prix,
        "weather": [
            {
                "timestamp": weather.ts.isoformat(),
                "temp_c": weather.temp_c,
                "wind_kph": weather.wind_kph,
                "precip_prob": weather.precip_prob,
                "precip_mm": weather.precip_mm,
                "cloud_pct": weather.cloud_pct,
                "humidity_pct": weather.humidity_pct,
                "pressure_hpa": weather.pressure_hpa,
                "track_wet": weather.track_wet
            } for weather in weather_data
        ]
    }