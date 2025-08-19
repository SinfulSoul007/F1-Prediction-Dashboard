from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ..models.database import get_db
from ..models.models import Race, Result, Circuit

router = APIRouter()

@router.get("/{year}")
async def get_season_results(year: int, db: Session = Depends(get_db)):
    """Get results archive for entire season"""
    races = db.query(Race).filter(Race.year == year).order_by(Race.round).all()
    
    season_results = []
    for race in races:
        results = db.query(Result).filter(Result.race_id == race.id).order_by(Result.finish_pos).all()
        circuit = db.query(Circuit).filter(Circuit.circuit_key == race.circuit_key).first()
        
        race_data = {
            "race_id": race.id,
            "round": race.round,
            "grand_prix": race.grand_prix,
            "race_date": race.race_date.isoformat() if race.race_date else None,
            "circuit": {
                "name": circuit.name,
                "locality": circuit.locality,
                "country": circuit.country
            } if circuit else None,
            "results": [
                {
                    "driver_code": result.driver_code,
                    "team": result.team,
                    "grid": result.grid,
                    "finish_pos": result.finish_pos,
                    "status": result.status,
                    "pit_stops": result.pit_stops
                } for result in results
            ]
        }
        season_results.append(race_data)
    
    return {"year": year, "races": season_results}

@router.get("/{year}/{round}")
async def get_race_results(year: int, round: int, db: Session = Depends(get_db)):
    """Get detailed results for specific race"""
    race = db.query(Race).filter(Race.year == year, Race.round == round).first()
    
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    
    results = db.query(Result).filter(Result.race_id == race.id).order_by(Result.finish_pos).all()
    circuit = db.query(Circuit).filter(Circuit.circuit_key == race.circuit_key).first()
    
    return {
        "race_id": race.id,
        "year": year,
        "round": round,
        "grand_prix": race.grand_prix,
        "race_date": race.race_date.isoformat() if race.race_date else None,
        "circuit": {
            "name": circuit.name,
            "locality": circuit.locality,
            "country": circuit.country,
            "latitude": circuit.latitude,
            "longitude": circuit.longitude
        } if circuit else None,
        "results": [
            {
                "driver_code": result.driver_code,
                "team": result.team,
                "grid": result.grid,
                "finish_pos": result.finish_pos,
                "status": result.status,
                "pit_stops": result.pit_stops,
                "total_time_ms": result.total_time_ms,
                "fastest_lap_ms": result.fastest_lap_ms,
                "tyre_stints": result.tyre_stints
            } for result in results
        ]
    }