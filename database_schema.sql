-- F1 Prediction Dashboard Database Schema
-- Run this script in Supabase SQL Editor to create all tables

-- Drop existing tables if they exist (in reverse dependency order)
DROP TABLE IF EXISTS prediction_accuracy CASCADE;
DROP TABLE IF EXISTS model_metrics CASCADE;
DROP TABLE IF EXISTS feature_importance CASCADE;
DROP TABLE IF EXISTS circuit_characteristics CASCADE;
DROP TABLE IF EXISTS team_performance CASCADE;
DROP TABLE IF EXISTS driver_performance CASCADE;
DROP TABLE IF EXISTS lap_data CASCADE;
DROP TABLE IF EXISTS predictions CASCADE;
DROP TABLE IF EXISTS weather CASCADE;
DROP TABLE IF EXISTS qualifying CASCADE;
DROP TABLE IF EXISTS results CASCADE;
DROP TABLE IF EXISTS races CASCADE;
DROP TABLE IF EXISTS circuits CASCADE;

-- Enable UUID extension for potential future use
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Circuits table - F1 track information
CREATE TABLE circuits (
    circuit_key VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200),
    locality VARCHAR(100),
    country VARCHAR(100),
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    type VARCHAR(50),
    distance_km DECIMAL(6, 3),
    laps INTEGER,
    drs_zones INTEGER,
    altitude_m DECIMAL(8, 2)
);

-- Races table - Race schedule and details
CREATE TABLE races (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    round INTEGER NOT NULL,
    circuit_key VARCHAR(50) REFERENCES circuits(circuit_key),
    grand_prix VARCHAR(200),
    race_date DATE,
    session_start TIMESTAMP WITH TIME ZONE,
    UNIQUE(year, round)
);

-- Results table - Race finishing results
CREATE TABLE results (
    race_id INTEGER REFERENCES races(id),
    driver_code VARCHAR(10),
    team VARCHAR(100),
    grid INTEGER,
    finish_pos INTEGER,
    status VARCHAR(50),
    pit_stops INTEGER,
    total_time_ms BIGINT,
    fastest_lap_ms INTEGER,
    tyre_stints TEXT,
    PRIMARY KEY (race_id, driver_code)
);

-- Qualifying table - Qualifying session results
CREATE TABLE qualifying (
    race_id INTEGER REFERENCES races(id),
    driver_code VARCHAR(10),
    team VARCHAR(100),
    q1_ms INTEGER,
    q2_ms INTEGER,
    q3_ms INTEGER,
    grid_penalty VARCHAR(100),
    quali_pos INTEGER,
    PRIMARY KEY (race_id, driver_code)
);

-- Weather table - Weather conditions for races
CREATE TABLE weather (
    race_id INTEGER REFERENCES races(id),
    ts TIMESTAMP WITH TIME ZONE,
    temp_c DECIMAL(5, 2),
    wind_kph DECIMAL(5, 2),
    precip_prob DECIMAL(5, 4),
    precip_mm DECIMAL(6, 3),
    cloud_pct INTEGER,
    humidity_pct INTEGER,
    pressure_hpa DECIMAL(7, 2),
    track_wet BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (race_id, ts)
);

-- Predictions table - ML prediction results
CREATE TABLE predictions (
    race_id INTEGER REFERENCES races(id),
    model_version VARCHAR(50),
    run_ts TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    params_json JSONB,
    predictions_json JSONB,
    metrics_json JSONB,
    PRIMARY KEY (race_id, model_version, run_ts)
);

-- Lap data table - Individual lap times and sectors
CREATE TABLE lap_data (
    id SERIAL PRIMARY KEY,
    race_id INTEGER REFERENCES races(id),
    driver_code VARCHAR(10),
    lap_number INTEGER,
    lap_time_ms INTEGER,
    sector1_time_ms INTEGER,
    sector2_time_ms INTEGER,
    sector3_time_ms INTEGER,
    compound VARCHAR(20),
    tyre_life INTEGER,
    is_deleted BOOLEAN DEFAULT FALSE,
    is_personal_best BOOLEAN DEFAULT FALSE
);

-- Driver performance table - Driver performance metrics
CREATE TABLE driver_performance (
    id SERIAL PRIMARY KEY,
    race_id INTEGER REFERENCES races(id),
    driver_code VARCHAR(10),
    team VARCHAR(100),
    clean_air_pace_ms INTEGER,
    clean_air_pace_rank INTEGER,
    avg_sector1_ms INTEGER,
    avg_sector2_ms INTEGER,
    avg_sector3_ms INTEGER,
    sector_consistency DECIMAL(8, 6),
    quali_time_ms INTEGER,
    quali_position INTEGER,
    quali_gap_to_pole_ms INTEGER,
    race_pace_ms INTEGER,
    positions_gained_lost INTEGER,
    fastest_lap_ms INTEGER,
    tire_degradation_rate DECIMAL(8, 6),
    stint_consistency DECIMAL(8, 6),
    wet_weather_factor DECIMAL(4, 3) DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Team performance table - Constructor/team metrics
CREATE TABLE team_performance (
    id SERIAL PRIMARY KEY,
    team VARCHAR(100),
    season_year INTEGER,
    constructor_points INTEGER DEFAULT 0,
    constructor_position INTEGER,
    avg_quali_position DECIMAL(5, 3),
    avg_race_position DECIMAL(5, 3),
    win_rate DECIMAL(5, 4) DEFAULT 0.0,
    podium_rate DECIMAL(5, 4) DEFAULT 0.0,
    points_per_race DECIMAL(6, 3) DEFAULT 0.0,
    dnf_rate DECIMAL(5, 4) DEFAULT 0.0,
    mechanical_issues INTEGER DEFAULT 0,
    avg_pit_stop_time_ms INTEGER,
    strategy_success_rate DECIMAL(5, 4) DEFAULT 0.0,
    recent_form_score DECIMAL(4, 3) DEFAULT 0.5,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(team, season_year)
);

-- Circuit characteristics table - Track-specific racing factors
CREATE TABLE circuit_characteristics (
    circuit_key VARCHAR(50) PRIMARY KEY REFERENCES circuits(circuit_key),
    overtaking_difficulty DECIMAL(4, 3) DEFAULT 0.5,
    qualifying_importance DECIMAL(4, 3) DEFAULT 0.7,
    track_evolution DECIMAL(4, 3) DEFAULT 0.5,
    weather_sensitivity DECIMAL(4, 3) DEFAULT 0.5,
    power_unit_sensitivity DECIMAL(4, 3) DEFAULT 0.5,
    aerodynamic_sensitivity DECIMAL(4, 3) DEFAULT 0.5,
    tire_wear_rate DECIMAL(4, 3) DEFAULT 0.5,
    tire_deg_sensitivity DECIMAL(4, 3) DEFAULT 0.5,
    safety_car_probability DECIMAL(4, 3) DEFAULT 0.2,
    lap_record_ms INTEGER,
    avg_race_time_ms INTEGER
);

-- Feature importance table - ML model feature analysis
CREATE TABLE feature_importance (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(50),
    feature_name VARCHAR(100),
    importance_score DECIMAL(8, 6),
    feature_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Model metrics table - ML model performance tracking
CREATE TABLE model_metrics (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(50),
    model_type VARCHAR(50),
    training_samples INTEGER,
    validation_samples INTEGER,
    mean_absolute_error DECIMAL(10, 6),
    root_mean_squared_error DECIMAL(10, 6),
    r2_score DECIMAL(8, 6),
    cv_mean_score DECIMAL(8, 6),
    cv_std_score DECIMAL(8, 6),
    hyperparameters JSONB,
    training_duration_seconds DECIMAL(10, 3),
    trained_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    trained_by VARCHAR(100) DEFAULT 'system',
    model_file_path VARCHAR(500),
    model_size_bytes INTEGER
);

-- Prediction accuracy table - Track prediction performance
CREATE TABLE prediction_accuracy (
    id SERIAL PRIMARY KEY,
    race_id INTEGER REFERENCES races(id),
    model_version VARCHAR(50),
    predicted_winner VARCHAR(10),
    actual_winner VARCHAR(10),
    winner_prediction_correct BOOLEAN,
    predicted_podium JSONB,
    actual_podium JSONB,
    podium_accuracy_score DECIMAL(5, 4),
    predicted_top10 JSONB,
    actual_top10 JSONB,
    top10_accuracy_score DECIMAL(5, 4),
    position_mae DECIMAL(6, 3),
    time_prediction_mae DECIMAL(10, 3),
    prediction_confidence DECIMAL(5, 4),
    uncertainty_score DECIMAL(5, 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_races_year_round ON races(year, round);
CREATE INDEX idx_races_circuit ON races(circuit_key);
CREATE INDEX idx_results_race_id ON results(race_id);
CREATE INDEX idx_qualifying_race_id ON qualifying(race_id);
CREATE INDEX idx_weather_race_id ON weather(race_id);
CREATE INDEX idx_weather_timestamp ON weather(ts);
CREATE INDEX idx_predictions_race_id ON predictions(race_id);
CREATE INDEX idx_lap_data_race_driver ON lap_data(race_id, driver_code);
CREATE INDEX idx_lap_data_race_lap ON lap_data(race_id, lap_number);
CREATE INDEX idx_driver_performance_race ON driver_performance(race_id);
CREATE INDEX idx_driver_performance_driver ON driver_performance(driver_code);
CREATE INDEX idx_team_performance_season ON team_performance(season_year);
CREATE INDEX idx_team_performance_team ON team_performance(team);
CREATE INDEX idx_feature_importance_model ON feature_importance(model_version);
CREATE INDEX idx_feature_importance_feature ON feature_importance(feature_name);
CREATE INDEX idx_model_metrics_version ON model_metrics(model_version);
CREATE INDEX idx_model_metrics_type ON model_metrics(model_type);
CREATE INDEX idx_model_metrics_trained ON model_metrics(trained_at);
CREATE INDEX idx_prediction_accuracy_race ON prediction_accuracy(race_id);
CREATE INDEX idx_prediction_accuracy_model ON prediction_accuracy(model_version);

-- Insert initial circuit data
INSERT INTO circuits (circuit_key, name, locality, country, latitude, longitude, type, distance_km, laps, drs_zones, altitude_m) VALUES
('bahrain', 'Bahrain International Circuit', 'Sakhir', 'Bahrain', 26.0325, 50.5106, 'permanent', 5.412, 57, 3, 7),
('jeddah', 'Jeddah Corniche Circuit', 'Jeddah', 'Saudi Arabia', 21.6319, 39.1044, 'street', 6.174, 50, 3, 15),
('albert_park', 'Albert Park Circuit', 'Melbourne', 'Australia', -37.8497, 144.968, 'street', 5.278, 58, 4, 12),
('suzuka', 'Suzuka International Racing Course', 'Suzuka', 'Japan', 34.8431, 136.5407, 'permanent', 5.807, 53, 2, 45),
('shanghai', 'Shanghai International Circuit', 'Shanghai', 'China', 31.3389, 121.2197, 'permanent', 5.451, 56, 2, 5),
('miami', 'Miami International Autodrome', 'Miami', 'United States', 25.9581, -80.2389, 'street', 5.41, 57, 3, 2),
('imola', 'Autodromo Enzo e Dino Ferrari', 'Imola', 'Italy', 44.3439, 11.7167, 'permanent', 4.909, 63, 2, 37),
('monaco', 'Circuit de Monaco', 'Monte Carlo', 'Monaco', 43.7347, 7.42056, 'street', 3.337, 78, 1, 42),
('barcelona', 'Circuit de Barcelona-Catalunya', 'Montmeló', 'Spain', 41.57, 2.26111, 'permanent', 4.675, 66, 2, 109),
('montreal', 'Circuit Gilles-Villeneuve', 'Montreal', 'Canada', 45.5, -73.5228, 'street', 4.361, 70, 1, 13),
('red_bull_ring', 'Red Bull Ring', 'Spielberg', 'Austria', 47.2197, 14.7647, 'permanent', 4.318, 71, 3, 678),
('silverstone', 'Silverstone Circuit', 'Silverstone', 'United Kingdom', 52.0786, -1.01694, 'permanent', 5.891, 52, 2, 153),
('hungaroring', 'Hungaroring', 'Budapest', 'Hungary', 47.5789, 19.2486, 'permanent', 4.381, 70, 1, 161),
('spa', 'Circuit de Spa-Francorchamps', 'Spa', 'Belgium', 50.4372, 5.97139, 'permanent', 7.004, 44, 3, 401),
('zandvoort', 'Circuit Park Zandvoort', 'Zandvoort', 'Netherlands', 52.3888, 4.54092, 'permanent', 4.259, 72, 3, 6),
('monza', 'Autodromo Nazionale di Monza', 'Monza', 'Italy', 45.6156, 9.28111, 'permanent', 5.793, 53, 3, 162),
('singapore', 'Marina Bay Street Circuit', 'Singapore', 'Singapore', 1.2914, 103.864, 'street', 5.063, 61, 3, 18),
('cota', 'Circuit of the Americas', 'Austin', 'United States', 30.1328, -97.6411, 'permanent', 5.513, 56, 2, 161),
('mexico', 'Autódromo Hermanos Rodríguez', 'Mexico City', 'Mexico', 19.4042, -99.0907, 'permanent', 4.304, 71, 3, 2229),
('interlagos', 'Autódromo José Carlos Pace', 'São Paulo', 'Brazil', -23.7036, -46.6997, 'permanent', 4.309, 71, 2, 760),
('vegas', 'Las Vegas Strip Circuit', 'Las Vegas', 'United States', 36.1147, -115.1728, 'street', 6.12, 50, 2, 610),
('losail', 'Losail International Circuit', 'Lusail', 'Qatar', 25.4892, 51.4542, 'permanent', 5.38, 57, 2, 9),
('yas_marina', 'Yas Marina Circuit', 'Abu Dhabi', 'United Arab Emirates', 24.4672, 54.6031, 'permanent', 5.281, 58, 2, 3);

-- Insert basic circuit characteristics
INSERT INTO circuit_characteristics (circuit_key, overtaking_difficulty, qualifying_importance, track_evolution, weather_sensitivity, safety_car_probability) VALUES
('monaco', 0.9, 0.95, 0.3, 0.7, 0.25),
('monza', 0.2, 0.6, 0.5, 0.4, 0.15),
('silverstone', 0.4, 0.7, 0.6, 0.8, 0.2),
('spa', 0.3, 0.7, 0.6, 0.8, 0.3),
('singapore', 0.6, 0.8, 0.4, 0.6, 0.4),
('bahrain', 0.5, 0.7, 0.5, 0.3, 0.2),
('suzuka', 0.6, 0.8, 0.5, 0.6, 0.25),
('cota', 0.4, 0.7, 0.6, 0.5, 0.2);

-- Success message
SELECT 'F1 Dashboard database schema created successfully! All tables and initial data have been set up.' AS message;