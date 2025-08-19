from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..models.database import get_db
from ..models.models import Race, Circuit
from ..services.prediction_service import prediction_service, PredictionWeights

router = APIRouter()

class PredictionRequest(BaseModel):
    weights: Dict[str, Any] = {
        "track_suitability": 0.85,
        "clean_air_pace": 0.90,
        "qualifying_importance": 0.85,
        "team_form": 0.68,
        "weather_impact": 0.45,
        "chaos_mode": False
    }

class DriverPredictionResponse(BaseModel):
    driver: str
    team: str
    predicted_time: float
    win_probability: float
    top3_probability: float
    
class PredictionResponse(BaseModel):
    race_id: int
    year: int
    round: int
    grand_prix: str
    circuit_name: str
    race_datetime: Optional[str]
    weights: Dict[str, Any]
    predictions: List[DriverPredictionResponse]
    feature_importance: Dict[str, float]
    model_confidence: float
    explanation: str

@router.post("/{year}/{round}", response_model=PredictionResponse)
async def predict_race(
    year: int, 
    round: int, 
    request: PredictionRequest,
    db: Session = Depends(get_db)
):
    """Generate race predictions with adjustable weights using ML model"""
    race = db.query(Race).filter(Race.year == year, Race.round == round).first()
    
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    
    # Get circuit information
    circuit = db.query(Circuit).filter(Circuit.circuit_key == race.circuit_key).first()
    circuit_name = circuit.name if circuit else "Unknown Circuit"
    
    try:
        # Convert request weights to PredictionWeights object
        weights = PredictionWeights(**request.weights)
        
        # Determine race datetime for weather forecasting
        race_datetime = None
        if race.session_start:
            race_datetime = race.session_start
        elif race.race_date:
            # If no session start time, estimate based on race date
            race_datetime = datetime.combine(race.race_date, datetime.min.time().replace(hour=14))
        
        # Get predictions from ML service
        predictions = await prediction_service.predict_race(
            year=year,
            event=circuit_name,
            round_num=round,
            weights=weights,
            race_datetime=race_datetime
        )
        
        # Get feature importance
        feature_importance = prediction_service.get_feature_importance()
        
        # Calculate model confidence (simplified)
        model_confidence = 0.85 if prediction_service.model else 0.45
        
        # Convert predictions to response format
        prediction_responses = [
            DriverPredictionResponse(
                driver=pred.driver,
                team=pred.team,
                predicted_time=pred.predicted_time,
                win_probability=pred.win_probability,
                top3_probability=pred.top3_probability
            )
            for pred in predictions
        ]
        
        # Generate explanation based on weights and conditions
        explanation = _generate_prediction_explanation(weights, race_datetime, feature_importance)
        
        return PredictionResponse(
            race_id=race.id,
            year=year,
            round=round,
            grand_prix=race.grand_prix,
            circuit_name=circuit_name,
            race_datetime=race_datetime.isoformat() if race_datetime else None,
            weights=request.weights,
            predictions=prediction_responses,
            feature_importance=feature_importance,
            model_confidence=model_confidence,
            explanation=explanation
        )
        
    except Exception as e:
        # Fallback to simplified predictions if ML service fails
        fallback_predictions = _create_fallback_predictions()
        
        return PredictionResponse(
            race_id=race.id,
            year=year,
            round=round,
            grand_prix=race.grand_prix,
            circuit_name=circuit_name,
            race_datetime=None,
            weights=request.weights,
            predictions=fallback_predictions,
            feature_importance={},
            model_confidence=0.3,
            explanation=f"Using fallback predictions due to ML service error: {str(e)}"
        )

@router.get("/feature-importance")
async def get_feature_importance():
    """Get current model feature importance"""
    try:
        importance = prediction_service.get_feature_importance()
        return {
            "feature_importance": importance,
            "model_available": prediction_service.model is not None,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting feature importance: {str(e)}")

@router.post("/train-model")
async def train_model(
    training_data: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    """Train the prediction model with historical data"""
    try:
        result = await prediction_service.train_model(training_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error training model: {str(e)}")

@router.get("/model-status")
async def get_model_status():
    """Get current model status and metrics"""
    try:
        return {
            "model_loaded": prediction_service.model is not None,
            "feature_count": len(prediction_service.feature_names),
            "feature_names": prediction_service.feature_names,
            "driver_count": len(prediction_service.driver_to_team),
            "team_count": len(prediction_service.team_performance_scores),
            "last_checked": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting model status: {str(e)}")

def _generate_prediction_explanation(weights: PredictionWeights, race_datetime: Optional[datetime], 
                                   feature_importance: Dict[str, float]) -> str:
    """Generate human-readable explanation of prediction factors"""
    explanations = []
    
    # Weight-based explanations
    if weights.track_suitability > 0.8:
        explanations.append("High track suitability weighting favors drivers with strong historical performance at this circuit")
    
    if weights.clean_air_pace > 0.8:
        explanations.append("Clean air pace is heavily weighted, benefiting drivers with strong one-lap pace")
    
    if weights.qualifying_importance > 0.8:
        explanations.append("Qualifying position is crucial - grid position heavily influences race outcome")
    
    if weights.weather_impact > 0.6:
        explanations.append("Weather conditions significantly impact the predictions")
    
    if weights.chaos_mode:
        explanations.append("Chaos mode enabled - increased unpredictability and variance in outcomes")
    
    # Feature importance explanations
    if feature_importance:
        top_feature = max(feature_importance.items(), key=lambda x: x[1])
        explanations.append(f"Most important prediction factor: {top_feature[0].replace('_', ' ').title()}")
    
    # Time-based explanations
    if race_datetime:
        hour = race_datetime.hour
        if hour < 10:
            explanations.append("Early race start may affect driver performance and strategy")
        elif hour > 18:
            explanations.append("Late race start increases likelihood of changing track conditions")
    
    if not explanations:
        explanations.append("Predictions based on historical performance, qualifying pace, and team form")
    
    return ". ".join(explanations) + "."

def _create_fallback_predictions() -> List[DriverPredictionResponse]:
    """Create fallback predictions when ML service is unavailable"""
    fallback_data = [
        {"driver": "VER", "team": "Red Bull", "time": 5400.0, "win_prob": 0.35, "top3_prob": 0.75},
        {"driver": "NOR", "team": "McLaren", "time": 5405.0, "win_prob": 0.25, "top3_prob": 0.65},
        {"driver": "LEC", "team": "Ferrari", "time": 5410.0, "win_prob": 0.15, "top3_prob": 0.55},
        {"driver": "PIA", "team": "McLaren", "time": 5412.0, "win_prob": 0.12, "top3_prob": 0.50},
        {"driver": "RUS", "team": "Mercedes", "time": 5415.0, "win_prob": 0.08, "top3_prob": 0.45},
        {"driver": "HAM", "team": "Mercedes", "time": 5418.0, "win_prob": 0.05, "top3_prob": 0.40}
    ]
    
    return [
        DriverPredictionResponse(
            driver=item["driver"],
            team=item["team"],
            predicted_time=item["time"],
            win_probability=item["win_prob"],
            top3_probability=item["top3_prob"]
        )
        for item in fallback_data
    ]