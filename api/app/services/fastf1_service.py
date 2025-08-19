import fastf1
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import os
from datetime import datetime, timedelta
import logging
from ..models.models import Race, Result, Qualifying

logger = logging.getLogger(__name__)

class FastF1Service:
    def __init__(self, cache_dir: str = ".fastf1_cache"):
        self.cache_dir = cache_dir
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        fastf1.Cache.enable_cache(cache_dir)
        
    async def get_session_data(self, year: int, event: str, session: str) -> Optional[fastf1.core.Session]:
        """
        Get FastF1 session data
        session: 'FP1', 'FP2', 'FP3', 'Q', 'R' (Race)
        """
        try:
            session_obj = fastf1.get_session(year, event, session)
            session_obj.load()
            return session_obj
        except Exception as e:
            logger.error(f"Error loading session {year} {event} {session}: {e}")
            return None

    async def get_lap_data(self, year: int, event: str, session: str = "R") -> Optional[pd.DataFrame]:
        """Get lap data for a session"""
        try:
            session_obj = await self.get_session_data(year, event, session)
            if session_obj is None:
                return None
                
            laps = session_obj.laps[["Driver", "LapTime", "Sector1Time", "Sector2Time", "Sector3Time"]].copy()
            laps.dropna(inplace=True)
            
            # Convert lap and sector times to seconds
            for col in ["LapTime", "Sector1Time", "Sector2Time", "Sector3Time"]:
                laps[f"{col}_seconds"] = laps[col].dt.total_seconds()
            
            return laps
        except Exception as e:
            logger.error(f"Error getting lap data: {e}")
            return None

    async def get_sector_times_by_driver(self, year: int, event: str, session: str = "R") -> Optional[pd.DataFrame]:
        """Get aggregated sector times by driver"""
        try:
            laps = await self.get_lap_data(year, event, session)
            if laps is None:
                return None
                
            # Aggregate sector times by driver
            sector_times = laps.groupby("Driver").agg({
                "Sector1Time_seconds": "mean",
                "Sector2Time_seconds": "mean", 
                "Sector3Time_seconds": "mean"
            }).reset_index()
            
            sector_times["TotalSectorTime_seconds"] = (
                sector_times["Sector1Time_seconds"] +
                sector_times["Sector2Time_seconds"] +
                sector_times["Sector3Time_seconds"]
            )
            
            return sector_times
        except Exception as e:
            logger.error(f"Error calculating sector times: {e}")
            return None

    async def get_clean_air_race_pace(self, year: int, event: str) -> Dict[str, float]:
        """
        Calculate clean air race pace for drivers
        Based on median clean laps methodology from sample
        """
        try:
            laps = await self.get_lap_data(year, event, "R")
            if laps is None:
                return {}
                
            # Filter for clean laps (this is simplified - in reality you'd need more sophisticated filtering)
            # Remove outliers (fastest 10% and slowest 10% per driver)
            clean_air_pace = {}
            
            for driver in laps["Driver"].unique():
                driver_laps = laps[laps["Driver"] == driver]["LapTime_seconds"]
                if len(driver_laps) > 0:
                    # Remove outliers
                    q1 = driver_laps.quantile(0.1)
                    q3 = driver_laps.quantile(0.9)
                    clean_laps = driver_laps[(driver_laps >= q1) & (driver_laps <= q3)]
                    
                    if len(clean_laps) > 0:
                        clean_air_pace[driver] = clean_laps.median()
            
            return clean_air_pace
        except Exception as e:
            logger.error(f"Error calculating clean air pace: {e}")
            return {}

    async def get_qualifying_results(self, year: int, event: str) -> Optional[pd.DataFrame]:
        """Get qualifying results"""
        try:
            session_obj = await self.get_session_data(year, event, "Q")
            if session_obj is None:
                return None
                
            results = session_obj.results
            if results is None or results.empty:
                return None
                
            # Extract relevant qualifying data
            quali_data = []
            for _, row in results.iterrows():
                driver_data = {
                    "Driver": row.get("Abbreviation", ""),
                    "Team": row.get("TeamName", ""),
                    "Q1": self._time_to_seconds(row.get("Q1")),
                    "Q2": self._time_to_seconds(row.get("Q2")), 
                    "Q3": self._time_to_seconds(row.get("Q3")),
                    "Position": row.get("Position", None),
                    "GridPosition": row.get("GridPosition", None)
                }
                quali_data.append(driver_data)
            
            return pd.DataFrame(quali_data)
        except Exception as e:
            logger.error(f"Error getting qualifying results: {e}")
            return None

    async def get_race_results(self, year: int, event: str) -> Optional[pd.DataFrame]:
        """Get race results"""
        try:
            session_obj = await self.get_session_data(year, event, "R")
            if session_obj is None:
                return None
                
            results = session_obj.results
            if results is None or results.empty:
                return None
                
            # Extract race results
            race_data = []
            for _, row in results.iterrows():
                driver_data = {
                    "Driver": row.get("Abbreviation", ""),
                    "Team": row.get("TeamName", ""),
                    "Position": row.get("Position", None),
                    "GridPosition": row.get("GridPosition", None),
                    "Time": self._time_to_seconds(row.get("Time")),
                    "Status": row.get("Status", ""),
                    "Points": row.get("Points", 0)
                }
                race_data.append(driver_data)
            
            return pd.DataFrame(race_data)
        except Exception as e:
            logger.error(f"Error getting race results: {e}")
            return None

    async def get_pit_stop_data(self, year: int, event: str) -> Optional[pd.DataFrame]:
        """Get pit stop data"""
        try:
            session_obj = await self.get_session_data(year, event, "R")
            if session_obj is None:
                return None
                
            pit_stops = session_obj.get_pitstops()
            if pit_stops is None or pit_stops.empty:
                return None
                
            return pit_stops
        except Exception as e:
            logger.error(f"Error getting pit stop data: {e}")
            return None

    def _time_to_seconds(self, time_obj) -> Optional[float]:
        """Convert time object to seconds"""
        if time_obj is None or pd.isna(time_obj):
            return None
            
        if hasattr(time_obj, 'total_seconds'):
            return time_obj.total_seconds()
        
        # Handle string format like "1:23.456"
        if isinstance(time_obj, str):
            try:
                if ":" in time_obj:
                    minutes, seconds = time_obj.split(":")
                    return float(minutes) * 60 + float(seconds)
                else:
                    return float(time_obj)
            except:
                return None
                
        return None

    async def get_driver_performance_metrics(self, year: int, event: str) -> Dict[str, Dict]:
        """
        Get comprehensive driver performance metrics for a race
        Similar to your sample code's feature engineering
        """
        try:
            # Get all the data we need
            lap_data = await self.get_lap_data(year, event, "R")
            quali_data = await self.get_qualifying_results(year, event)
            race_results = await self.get_race_results(year, event)
            clean_air_pace = await self.get_clean_air_race_pace(year, event)
            sector_times = await self.get_sector_times_by_driver(year, event, "R")
            
            metrics = {}
            
            if lap_data is not None:
                for driver in lap_data["Driver"].unique():
                    driver_metrics = {
                        "driver": driver,
                        "clean_air_pace": clean_air_pace.get(driver),
                        "average_lap_time": lap_data[lap_data["Driver"] == driver]["LapTime_seconds"].mean(),
                        "lap_count": len(lap_data[lap_data["Driver"] == driver]),
                        "sector_performance": {}
                    }
                    
                    # Add sector times
                    if sector_times is not None:
                        sector_row = sector_times[sector_times["Driver"] == driver]
                        if not sector_row.empty:
                            driver_metrics["sector_performance"] = {
                                "sector1": sector_row["Sector1Time_seconds"].iloc[0],
                                "sector2": sector_row["Sector2Time_seconds"].iloc[0],
                                "sector3": sector_row["Sector3Time_seconds"].iloc[0],
                                "total": sector_row["TotalSectorTime_seconds"].iloc[0]
                            }
                    
                    # Add qualifying position
                    if quali_data is not None:
                        quali_row = quali_data[quali_data["Driver"] == driver]
                        if not quali_row.empty:
                            driver_metrics["qualifying_position"] = quali_row["Position"].iloc[0]
                            driver_metrics["qualifying_time"] = quali_row["Q3"].iloc[0] or quali_row["Q2"].iloc[0] or quali_row["Q1"].iloc[0]
                    
                    # Add race results
                    if race_results is not None:
                        result_row = race_results[race_results["Driver"] == driver]
                        if not result_row.empty:
                            driver_metrics["finish_position"] = result_row["Position"].iloc[0]
                            driver_metrics["grid_position"] = result_row["GridPosition"].iloc[0]
                            driver_metrics["race_time"] = result_row["Time"].iloc[0]
                            driver_metrics["status"] = result_row["Status"].iloc[0]
                            driver_metrics["points"] = result_row["Points"].iloc[0]
                    
                    metrics[driver] = driver_metrics
            
            return metrics
        except Exception as e:
            logger.error(f"Error calculating driver performance metrics: {e}")
            return {}

    async def get_track_characteristics(self, event: str) -> Dict[str, float]:
        """
        Get track characteristics that affect racing
        This would be enhanced with more sophisticated analysis
        """
        # This is a simplified implementation - in reality you'd analyze track data
        track_characteristics = {
            "Monaco": {
                "overtaking_difficulty": 0.9,  # Very difficult
                "qualifying_importance": 0.95,
                "track_evolution": 0.3,
                "weather_sensitivity": 0.7
            },
            "Monza": {
                "overtaking_difficulty": 0.2,  # Easy
                "qualifying_importance": 0.6,
                "track_evolution": 0.5,
                "weather_sensitivity": 0.4
            },
            "Silverstone": {
                "overtaking_difficulty": 0.4,
                "qualifying_importance": 0.7,
                "track_evolution": 0.6,
                "weather_sensitivity": 0.8
            }
        }
        
        return track_characteristics.get(event, {
            "overtaking_difficulty": 0.5,
            "qualifying_importance": 0.7,
            "track_evolution": 0.5,
            "weather_sensitivity": 0.5
        })

# Service instance
fastf1_service = FastF1Service(
    cache_dir=os.getenv("FASTF1_CACHE_DIR", ".fastf1_cache")
)