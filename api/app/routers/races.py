from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models.database import get_db
from ..models.models import Race, Circuit, Result, Qualifying

router = APIRouter()

@router.get("/{year}/{round}")
async def get_race_overview(year: int, round: int, db: Session = Depends(get_db)):
    """Get race overview and results if available"""
    race = db.query(Race).filter(Race.year == year, Race.round == round).first()
    
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    
    circuit = db.query(Circuit).filter(Circuit.circuit_key == race.circuit_key).first()
    results = db.query(Result).filter(Result.race_id == race.id).order_by(Result.finish_pos).all()
    
    race_data = {
        "id": race.id,
        "year": race.year,
        "round": race.round,
        "grand_prix": race.grand_prix,
        "race_date": race.race_date.isoformat() if race.race_date else None,
        "session_start": race.session_start.isoformat() if race.session_start else None,
        "circuit": {
            "circuit_key": circuit.circuit_key,
            "name": circuit.name,
            "locality": circuit.locality,
            "country": circuit.country,
            "latitude": circuit.latitude,
            "longitude": circuit.longitude,
            "distance_km": circuit.distance_km,
            "laps": circuit.laps
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
                "fastest_lap_ms": result.fastest_lap_ms
            } for result in results
        ]
    }
    
    return race_data

@router.get("/{year}/{round}/laps")
async def get_race_laps(year: int, round: int, session: str = "R", db: Session = Depends(get_db)):
    """Get lap data for a specific session (R=Race, Q=Qualifying, FP1/FP2/FP3)"""
    race = db.query(Race).filter(Race.year == year, Race.round == round).first()
    
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    
    # TODO: Implement lap data retrieval from FastF1
    # This will be implemented with the FastF1 service
    return {"message": "Lap data retrieval not yet implemented", "race_id": race.id, "session": session}