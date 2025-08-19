import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from sklearn.impute import SimpleImputer
import pickle
import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from .fastf1_service import fastf1_service
from .weather_service import weather_service, WeatherData

logger = logging.getLogger(__name__)

class PredictionWeights:
    def __init__(self, **kwargs):
        self.track_suitability = kwargs.get("track_suitability", 0.85)
        self.clean_air_pace = kwargs.get("clean_air_pace", 0.90)
        self.qualifying_importance = kwargs.get("qualifying_importance", 0.85)
        self.team_form = kwargs.get("team_form", 0.68)
        self.weather_impact = kwargs.get("weather_impact", 0.45)
        self.chaos_mode = kwargs.get("chaos_mode", False)

class DriverPrediction:
    def __init__(self, driver: str, team: str, predicted_time: float, win_probability: float, top3_probability: float):
        self.driver = driver
        self.team = team
        self.predicted_time = predicted_time
        self.win_probability = win_probability
        self.top3_probability = top3_probability

class PredictionService:
    def __init__(self):
        self.model = None
        self.imputer = None
        self.feature_names = [
            "qualifying_time",
            "rain_probability", 
            "temperature",
            "team_performance_score",
            "clean_air_pace",
            "average_position_change"
        ]
        self.driver_to_team = {
            "VER": "Red Bull", "NOR": "McLaren", "PIA": "McLaren", "LEC": "Ferrari", 
            "RUS": "Mercedes", "HAM": "Mercedes", "GAS": "Alpine", "ALO": "Aston Martin",
            "TSU": "Racing Bulls", "SAI": "Ferrari", "HUL": "Kick Sauber", "OCO": "Alpine", 
            "STR": "Aston Martin", "ALB": "Williams", "COL": "Williams", "MAG": "Haas",
            "BOT": "Kick Sauber", "ZHO": "Kick Sauber", "RIC": "Racing Bulls"
        }
        
        # Team performance scores (could be loaded from database)
        self.team_performance_scores = {
            "McLaren": 279/279, "Mercedes": 147/279, "Red Bull": 131/279, "Williams": 51/279,
            "Ferrari": 114/279, "Haas": 20/279, "Aston Martin": 14/279, "Kick Sauber": 6/279,
            "Racing Bulls": 10/279, "Alpine": 7/279
        }
        
        # Average position change by circuit (from your sample)
        self.average_position_change = {
            "Monaco": {
                "VER": -1.0, "NOR": 1.0, "PIA": 0.2, "RUS": 0.5, "SAI": -0.3,
                "ALB": 0.8, "LEC": -1.5, "OCO": -0.2, "HAM": 0.3, "STR": 1.1,
                "GAS": -0.4, "ALO": -0.6, "HUL": 0.0
            }
        }

        self.load_model()

    def load_model(self):
        """Load trained model or create new one"""
        model_path = "models/race_prediction_model.pkl"
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.model = model_data['model']
                    self.imputer = model_data['imputer']
                    logger.info("Loaded existing prediction model")
                    return
            except Exception as e:
                logger.error(f"Error loading model: {e}")
        
        # Create new model if none exists
        self._create_default_model()

    def _create_default_model(self):
        """Create a default model for initial predictions"""
        self.model = GradientBoostingRegressor(
            n_estimators=100, 
            learning_rate=0.7, 
            max_depth=3, 
            random_state=37
        )
        self.imputer = SimpleImputer(strategy="median")
        logger.info("Created default prediction model")

    async def predict_race(self, year: int, event: str, round_num: int, 
                          weights: PredictionWeights, 
                          race_datetime: Optional[datetime] = None) -> List[DriverPrediction]:
        """
        Main prediction function based on your sample approach
        """
        try:
            # Get weather data
            weather_data = None
            if race_datetime:
                weather_data = await weather_service.get_weather_forecast(event, race_datetime)
            
            if not weather_data:
                # Use default weather if no forecast available
                weather_data = WeatherData(
                    timestamp=datetime.now(),
                    temperature_c=20.0,
                    wind_kph=10.0,
                    precipitation_prob=0.1,
                    precipitation_mm=0.0,
                    cloud_percentage=30,
                    humidity_percentage=60,
                    pressure_hpa=1013.25,
                    weather_condition="clear",
                    is_wet=False
                )

            # Get historical data for the circuit
            clean_air_pace = await self._get_clean_air_pace_data(year, event)
            qualifying_data = await self._get_qualifying_predictions(year, event)
            
            # Build features for each driver
            driver_features = []
            drivers = []
            
            for driver, team in self.driver_to_team.items():
                features = self._build_driver_features(
                    driver, team, event, weather_data, 
                    clean_air_pace, qualifying_data, weights
                )
                
                if features is not None:
                    driver_features.append(features)
                    drivers.append(driver)

            if not driver_features:
                logger.warning("No driver features available for prediction")
                return []

            # Convert to DataFrame and make predictions
            features_df = pd.DataFrame(driver_features, columns=self.feature_names)
            
            # Handle missing values
            if self.imputer is None:
                self.imputer = SimpleImputer(strategy="median")
                features_imputed = self.imputer.fit_transform(features_df)
            else:
                features_imputed = self.imputer.transform(features_df)

            # Make predictions
            if self.model is None:
                # If no model, create mock predictions based on features
                predicted_times = self._create_mock_predictions(features_df, drivers)
            else:
                predicted_times = self.model.predict(features_imputed)

            # Apply weight adjustments (your overlay approach)
            adjusted_times = self._apply_weight_adjustments(
                predicted_times, features_df, drivers, weights
            )

            # Convert to probabilities and create results
            predictions = self._times_to_predictions(drivers, adjusted_times)
            
            return sorted(predictions, key=lambda x: x.predicted_time)

        except Exception as e:
            logger.error(f"Error in race prediction: {e}")
            return []

    def _build_driver_features(self, driver: str, team: str, event: str, 
                              weather_data: WeatherData, clean_air_pace: Dict,
                              qualifying_data: Dict, weights: PredictionWeights) -> Optional[List[float]]:
        """Build feature vector for a driver"""
        try:
            # Qualifying time (mock data if not available)
            quali_time = qualifying_data.get(driver, self._estimate_qualifying_time(driver, team))
            
            # Team performance score
            team_score = self.team_performance_scores.get(team, 0.5)
            
            # Clean air pace
            pace = clean_air_pace.get(driver, self._estimate_clean_air_pace(driver, team))
            
            # Average position change for circuit
            position_change = self.average_position_change.get(event, {}).get(driver, 0.0)
            
            features = [
                quali_time,
                weather_data.precipitation_prob,
                weather_data.temperature_c,
                team_score,
                pace,
                position_change
            ]
            
            return features
            
        except Exception as e:
            logger.error(f"Error building features for {driver}: {e}")
            return None

    async def _get_clean_air_pace_data(self, year: int, event: str) -> Dict[str, float]:
        """Get clean air pace data or use estimates"""
        try:
            # Try to get from FastF1
            pace_data = await fastf1_service.get_clean_air_race_pace(year, event)
            if pace_data:
                return pace_data
        except:
            pass
        
        # Use mock data based on your sample
        return {
            "VER": 93.191, "HAM": 94.021, "LEC": 93.419, "NOR": 93.429, "ALO": 94.784,
            "PIA": 93.232, "RUS": 93.833, "SAI": 94.497, "STR": 95.318, "HUL": 95.345,
            "OCO": 95.682, "GAS": 95.9, "TSU": 96.1, "ALB": 95.8, "MAG": 96.2,
            "BOT": 96.5, "ZHO": 96.8, "RIC": 95.7, "COL": 96.0
        }

    async def _get_qualifying_predictions(self, year: int, event: str) -> Dict[str, float]:
        """Get qualifying data or predictions"""
        try:
            # Try to get actual qualifying results
            quali_results = await fastf1_service.get_qualifying_results(year, event)
            if quali_results is not None and not quali_results.empty:
                quali_dict = {}
                for _, row in quali_results.iterrows():
                    driver = row["Driver"]
                    time = row["Q3"] or row["Q2"] or row["Q1"]
                    if time:
                        quali_dict[driver] = time
                return quali_dict
        except:
            pass
        
        # Use estimated qualifying times based on team performance
        return {driver: self._estimate_qualifying_time(driver, team) 
                for driver, team in self.driver_to_team.items()}

    def _estimate_qualifying_time(self, driver: str, team: str) -> float:
        """Estimate qualifying time based on team performance"""
        base_times = {
            "Red Bull": 70.5, "McLaren": 70.8, "Ferrari": 71.0, "Mercedes": 71.2,
            "Aston Martin": 71.5, "Alpine": 71.8, "Williams": 72.0, "Racing Bulls": 72.2,
            "Haas": 72.4, "Kick Sauber": 72.6
        }
        
        base_time = base_times.get(team, 72.5)
        
        # Add driver-specific adjustment
        driver_adjustments = {
            "VER": -0.3, "NOR": -0.1, "LEC": -0.2, "HAM": -0.1, "RUS": 0.0,
            "PIA": 0.1, "ALO": -0.1, "SAI": 0.0, "STR": 0.2, "GAS": 0.1
        }
        
        adjustment = driver_adjustments.get(driver, 0.0)
        return base_time + adjustment + np.random.normal(0, 0.1)

    def _estimate_clean_air_pace(self, driver: str, team: str) -> float:
        """Estimate clean air pace"""
        base_pace = {
            "Red Bull": 93.5, "McLaren": 93.7, "Ferrari": 94.0, "Mercedes": 94.2,
            "Aston Martin": 95.0, "Alpine": 95.5, "Williams": 95.8, "Racing Bulls": 96.0,
            "Haas": 96.2, "Kick Sauber": 96.5
        }
        
        return base_pace.get(team, 96.0) + np.random.normal(0, 0.2)

    def _create_mock_predictions(self, features_df: pd.DataFrame, drivers: List[str]) -> np.ndarray:
        """Create mock predictions when no trained model exists"""
        # Simple prediction based on qualifying time and team performance
        predictions = []
        for _, row in features_df.iterrows():
            base_time = row["qualifying_time"] + 20  # Add typical race time delta
            team_factor = row["team_performance_score"]
            weather_factor = 1 + (row["rain_probability"] * 0.1)  # Rain adds time
            
            predicted_time = base_time * (2 - team_factor) * weather_factor
            predictions.append(predicted_time)
        
        return np.array(predictions)

    def _apply_weight_adjustments(self, predicted_times: np.ndarray, features_df: pd.DataFrame, 
                                 drivers: List[str], weights: PredictionWeights) -> np.ndarray:
        """
        Apply weight adjustments to predictions (your overlay approach)
        """
        adjusted_times = predicted_times.copy()
        
        for i, (time, driver) in enumerate(zip(predicted_times, drivers)):
            # Calculate z-scores for different features
            z_track = self._calculate_z_score(features_df["average_position_change"].iloc[i])
            z_pace = self._calculate_z_score(features_df["clean_air_pace"].iloc[i])
            z_quali = self._calculate_z_score(features_df["qualifying_time"].iloc[i])
            z_team = self._calculate_z_score(features_df["team_performance_score"].iloc[i])
            z_weather = self._calculate_z_score(features_df["rain_probability"].iloc[i])
            
            # Apply weighted adjustments
            adjustment = (
                weights.track_suitability * z_track * 0.1 +
                weights.clean_air_pace * z_pace * 0.1 +
                weights.qualifying_importance * z_quali * 0.1 +
                weights.team_form * z_team * 0.1 +
                weights.weather_impact * z_weather * 0.1
            )
            
            adjusted_times[i] = time + adjustment
            
            # Add chaos if enabled
            if weights.chaos_mode:
                chaos_noise = np.random.normal(0, 2.0)  # 2 second standard deviation
                adjusted_times[i] += chaos_noise
        
        return adjusted_times

    def _calculate_z_score(self, value: float, mean: float = 0.0, std: float = 1.0) -> float:
        """Calculate z-score for normalization"""
        if std == 0:
            return 0.0
        return (value - mean) / std

    def _times_to_predictions(self, drivers: List[str], predicted_times: np.ndarray) -> List[DriverPrediction]:
        """Convert predicted times to prediction objects with probabilities"""
        predictions = []
        
        # Sort to get ranking
        sorted_indices = np.argsort(predicted_times)
        
        for i, idx in enumerate(sorted_indices):
            driver = drivers[idx]
            team = self.driver_to_team.get(driver, "Unknown")
            time = predicted_times[idx]
            
            # Calculate win probability (higher for better positions)
            win_prob = max(0.01, 0.95 - (i * 0.05))
            
            # Calculate top 3 probability
            if i < 3:
                top3_prob = 0.8 - (i * 0.1)
            else:
                top3_prob = max(0.05, 0.5 - ((i - 3) * 0.05))
            
            predictions.append(DriverPrediction(
                driver=driver,
                team=team,
                predicted_time=time,
                win_probability=win_prob,
                top3_probability=top3_prob
            ))
        
        return predictions

    async def train_model(self, training_data: List[Dict]) -> Dict[str, float]:
        """Train the prediction model with historical data"""
        try:
            if not training_data:
                logger.warning("No training data provided")
                return {"error": "No training data"}
            
            # Convert training data to features and targets
            X = []
            y = []
            
            for race_data in training_data:
                features = race_data.get("features", [])
                actual_time = race_data.get("actual_time")
                
                if len(features) == len(self.feature_names) and actual_time is not None:
                    X.append(features)
                    y.append(actual_time)
            
            if len(X) < 10:  # Need minimum amount of data
                logger.warning("Insufficient training data")
                return {"error": "Insufficient training data"}
            
            X = np.array(X)
            y = np.array(y)
            
            # Prepare data
            self.imputer = SimpleImputer(strategy="median")
            X_imputed = self.imputer.fit_transform(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_imputed, y, test_size=0.3, random_state=37
            )
            
            # Train model
            self.model = GradientBoostingRegressor(
                n_estimators=100, 
                learning_rate=0.7, 
                max_depth=3, 
                random_state=37
            )
            
            self.model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = self.model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            
            # Save model
            self._save_model()
            
            # Get feature importances
            feature_importance = {
                name: importance 
                for name, importance in zip(self.feature_names, self.model.feature_importances_)
            }
            
            logger.info(f"Model trained successfully. MAE: {mae:.2f}")
            
            return {
                "status": "success",
                "mae": mae,
                "feature_importance": feature_importance,
                "training_samples": len(X),
                "test_samples": len(X_test)
            }
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return {"error": str(e)}

    def _save_model(self):
        """Save trained model to disk"""
        try:
            os.makedirs("models", exist_ok=True)
            model_data = {
                "model": self.model,
                "imputer": self.imputer,
                "feature_names": self.feature_names,
                "trained_at": datetime.now().isoformat()
            }
            
            with open("models/race_prediction_model.pkl", "wb") as f:
                pickle.dump(model_data, f)
                
            logger.info("Model saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model"""
        if self.model is None:
            return {}
        
        return {
            name: importance 
            for name, importance in zip(self.feature_names, self.model.feature_importances_)
        }

# Service instance
prediction_service = PredictionService()