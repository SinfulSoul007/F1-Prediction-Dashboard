from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..models.database import get_db
from ..models.models import Race, Circuit

router = APIRouter()

@router.get("/{year}/races")
async def get_season_races(year: int, db: Session = Depends(get_db)):
    """Get all races for a specific season"""
    races = db.query(Race).filter(Race.year == year).order_by(Race.round).all()
    
    race_list = []
    for race in races:
        circuit = db.query(Circuit).filter(Circuit.circuit_key == race.circuit_key).first()
        race_data = {
            "id": race.id,
            "round": race.round,
            "grand_prix": race.grand_prix,
            "race_date": race.race_date.isoformat() if race.race_date else None,
            "session_start": race.session_start.isoformat() if race.session_start else None,
            "circuit": {
                "circuit_key": circuit.circuit_key if circuit else None,
                "name": circuit.name if circuit else None,
                "locality": circuit.locality if circuit else None,
                "country": circuit.country if circuit else None,
                "latitude": circuit.latitude if circuit else None,
                "longitude": circuit.longitude if circuit else None
            } if circuit else None
        }
        race_list.append(race_data)
    
    return {"year": year, "races": race_list}

@router.get("/")
async def get_available_seasons(db: Session = Depends(get_db)):
    """Get list of available seasons"""
    years = db.query(Race.year).distinct().order_by(Race.year.desc()).all()
    return {"seasons": [year[0] for year in years]}