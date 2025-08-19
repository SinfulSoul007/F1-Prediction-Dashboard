from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, JSON, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Circuit(Base):
    __tablename__ = "circuits"
    
    circuit_key = Column(String, primary_key=True)
    name = Column(String)
    locality = Column(String)
    country = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    type = Column(String)
    distance_km = Column(Float)
    laps = Column(Integer)
    drs_zones = Column(Integer)
    altitude_m = Column(Float)
    
    # Relationship
    races = relationship("Race", back_populates="circuit")

class Race(Base):
    __tablename__ = "races"
    
    id = Column(Integer, primary_key=True)
    year = Column(Integer)
    round = Column(Integer)
    circuit_key = Column(String, ForeignKey("circuits.circuit_key"))
    grand_prix = Column(String)
    race_date = Column(Date)
    session_start = Column(DateTime)
    
    # Relationships
    circuit = relationship("Circuit", back_populates="races")
    results = relationship("Result", back_populates="race")
    qualifying = relationship("Qualifying", back_populates="race")
    weather = relationship("Weather", back_populates="race")
    predictions = relationship("Prediction", back_populates="race")

class Result(Base):
    __tablename__ = "results"
    
    race_id = Column(Integer, ForeignKey("races.id"), primary_key=True)
    driver_code = Column(String, primary_key=True)
    team = Column(String)
    grid = Column(Integer)
    finish_pos = Column(Integer)
    status = Column(String)
    pit_stops = Column(Integer)
    total_time_ms = Column(Integer)
    fastest_lap_ms = Column(Integer)
    tyre_stints = Column(Text)
    
    # Relationship
    race = relationship("Race", back_populates="results")

class Qualifying(Base):
    __tablename__ = "qualifying"
    
    race_id = Column(Integer, ForeignKey("races.id"), primary_key=True)
    driver_code = Column(String, primary_key=True)
    team = Column(String)
    q1_ms = Column(Integer)
    q2_ms = Column(Integer)
    q3_ms = Column(Integer)
    grid_penalty = Column(String)
    quali_pos = Column(Integer)
    
    # Relationship
    race = relationship("Race", back_populates="qualifying")

class Weather(Base):
    __tablename__ = "weather"
    
    race_id = Column(Integer, ForeignKey("races.id"), primary_key=True)
    ts = Column(DateTime, primary_key=True)
    temp_c = Column(Float)
    wind_kph = Column(Float)
    precip_prob = Column(Float)
    precip_mm = Column(Float)
    cloud_pct = Column(Integer)
    humidity_pct = Column(Integer)
    pressure_hpa = Column(Float)
    track_wet = Column(Boolean)
    
    # Relationship
    race = relationship("Race", back_populates="weather")

class Prediction(Base):
    __tablename__ = "predictions"
    
    race_id = Column(Integer, ForeignKey("races.id"), primary_key=True)
    model_version = Column(String, primary_key=True)
    run_ts = Column(DateTime, primary_key=True)
    params_json = Column(JSON)
    predictions_json = Column(JSON)
    metrics_json = Column(JSON)
    
    # Relationship
    race = relationship("Race", back_populates="predictions")

class LapData(Base):
    __tablename__ = "lap_data"
    
    id = Column(Integer, primary_key=True)
    race_id = Column(Integer, ForeignKey("races.id"))
    driver_code = Column(String)
    lap_number = Column(Integer)
    lap_time_ms = Column(Integer)
    sector1_time_ms = Column(Integer)
    sector2_time_ms = Column(Integer)
    sector3_time_ms = Column(Integer)
    compound = Column(String)
    tyre_life = Column(Integer)
    is_deleted = Column(Boolean, default=False)
    is_personal_best = Column(Boolean, default=False)
    
    # Index for performance
    __table_args__ = (
        Index('idx_lap_data_race_driver', 'race_id', 'driver_code'),
        Index('idx_lap_data_race_lap', 'race_id', 'lap_number'),
    )

class DriverPerformance(Base):
    __tablename__ = "driver_performance"
    
    id = Column(Integer, primary_key=True)
    race_id = Column(Integer, ForeignKey("races.id"))
    driver_code = Column(String)
    team = Column(String)
    
    # Clean air pace metrics
    clean_air_pace_ms = Column(Integer)
    clean_air_pace_rank = Column(Integer)
    
    # Sector performance
    avg_sector1_ms = Column(Integer)
    avg_sector2_ms = Column(Integer)
    avg_sector3_ms = Column(Integer)
    sector_consistency = Column(Float)
    
    # Qualifying performance
    quali_time_ms = Column(Integer)
    quali_position = Column(Integer)
    quali_gap_to_pole_ms = Column(Integer)
    
    # Race performance
    race_pace_ms = Column(Integer)
    positions_gained_lost = Column(Integer)
    fastest_lap_ms = Column(Integer)
    
    # Tire performance
    tire_degradation_rate = Column(Float)
    stint_consistency = Column(Float)
    
    # Weather adjustment factors
    wet_weather_factor = Column(Float, default=1.0)
    
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_driver_performance_race', 'race_id'),
        Index('idx_driver_performance_driver', 'driver_code'),
    )

class TeamPerformance(Base):
    __tablename__ = "team_performance"
    
    id = Column(Integer, primary_key=True)
    team = Column(String)
    season_year = Column(Integer)
    
    # Championship points
    constructor_points = Column(Integer, default=0)
    constructor_position = Column(Integer)
    
    # Performance metrics
    avg_quali_position = Column(Float)
    avg_race_position = Column(Float)
    win_rate = Column(Float, default=0.0)
    podium_rate = Column(Float, default=0.0)
    points_per_race = Column(Float, default=0.0)
    
    # Reliability metrics
    dnf_rate = Column(Float, default=0.0)
    mechanical_issues = Column(Integer, default=0)
    
    # Strategy metrics
    avg_pit_stop_time_ms = Column(Integer)
    strategy_success_rate = Column(Float, default=0.0)
    
    # Recent form (last 5 races)
    recent_form_score = Column(Float, default=0.5)
    
    updated_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_team_performance_season', 'season_year'),
        Index('idx_team_performance_team', 'team'),
    )

class CircuitCharacteristics(Base):
    __tablename__ = "circuit_characteristics"
    
    circuit_key = Column(String, ForeignKey("circuits.circuit_key"), primary_key=True)
    
    # Track characteristics affecting racing
    overtaking_difficulty = Column(Float, default=0.5)  # 0 = easy, 1 = very difficult
    qualifying_importance = Column(Float, default=0.7)   # How much quali position matters
    track_evolution = Column(Float, default=0.5)         # How much track improves during weekend
    weather_sensitivity = Column(Float, default=0.5)     # How much weather affects performance
    
    # Power unit importance
    power_unit_sensitivity = Column(Float, default=0.5)
    aerodynamic_sensitivity = Column(Float, default=0.5)
    
    # Tire characteristics
    tire_wear_rate = Column(Float, default=0.5)
    tire_deg_sensitivity = Column(Float, default=0.5)
    
    # Safety car probability
    safety_car_probability = Column(Float, default=0.2)
    
    # Historical data
    lap_record_ms = Column(Integer)
    avg_race_time_ms = Column(Integer)
    
    # Relationship
    circuit = relationship("Circuit")

class FeatureImportance(Base):
    __tablename__ = "feature_importance"
    
    id = Column(Integer, primary_key=True)
    model_version = Column(String)
    feature_name = Column(String)
    importance_score = Column(Float)
    feature_type = Column(String)  # 'driver', 'weather', 'track', 'team'
    
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_feature_importance_model', 'model_version'),
        Index('idx_feature_importance_feature', 'feature_name'),
    )

class ModelMetrics(Base):
    __tablename__ = "model_metrics"
    
    id = Column(Integer, primary_key=True)
    model_version = Column(String)
    model_type = Column(String)  # 'race_time', 'win_probability', 'position'
    
    # Training metrics
    training_samples = Column(Integer)
    validation_samples = Column(Integer)
    mean_absolute_error = Column(Float)
    root_mean_squared_error = Column(Float)
    r2_score = Column(Float)
    
    # Cross-validation metrics
    cv_mean_score = Column(Float)
    cv_std_score = Column(Float)
    
    # Model parameters
    hyperparameters = Column(JSON)
    
    # Training metadata
    training_duration_seconds = Column(Float)
    trained_at = Column(DateTime, default=func.now())
    trained_by = Column(String, default='system')
    
    # Model file information
    model_file_path = Column(String)
    model_size_bytes = Column(Integer)
    
    __table_args__ = (
        Index('idx_model_metrics_version', 'model_version'),
        Index('idx_model_metrics_type', 'model_type'),
        Index('idx_model_metrics_trained', 'trained_at'),
    )

class PredictionAccuracy(Base):
    __tablename__ = "prediction_accuracy"
    
    id = Column(Integer, primary_key=True)
    race_id = Column(Integer, ForeignKey("races.id"))
    model_version = Column(String)
    
    # Prediction vs actual comparison
    predicted_winner = Column(String)
    actual_winner = Column(String)
    winner_prediction_correct = Column(Boolean)
    
    predicted_podium = Column(JSON)  # List of driver codes
    actual_podium = Column(JSON)     # List of driver codes
    podium_accuracy_score = Column(Float)  # 0-1 score
    
    predicted_top10 = Column(JSON)
    actual_top10 = Column(JSON)
    top10_accuracy_score = Column(Float)
    
    # Overall prediction quality
    position_mae = Column(Float)  # Mean absolute error for positions
    time_prediction_mae = Column(Float)  # MAE for time predictions
    
    # Confidence metrics
    prediction_confidence = Column(Float)
    uncertainty_score = Column(Float)
    
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_prediction_accuracy_race', 'race_id'),
        Index('idx_prediction_accuracy_model', 'model_version'),
    )