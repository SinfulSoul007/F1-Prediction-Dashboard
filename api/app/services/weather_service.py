import httpx
import os
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class WeatherData(BaseModel):
    timestamp: datetime
    temperature_c: float
    wind_kph: float
    precipitation_prob: float
    precipitation_mm: float
    cloud_percentage: int
    humidity_percentage: int
    pressure_hpa: float
    weather_condition: str
    is_wet: bool

class CircuitLocation(BaseModel):
    name: str
    latitude: float
    longitude: float

class WeatherService:
    def __init__(self):
        self.openweather_api_key = os.getenv("OPENWEATHER_API_KEY")
        self.weather_provider = os.getenv("WEATHER_PROVIDER", "open-meteo")
        
        # Circuit locations for weather data
        self.circuit_locations = {
            "Monaco": CircuitLocation(name="Monaco", latitude=43.7384, longitude=7.4246),
            "Silverstone": CircuitLocation(name="Silverstone", latitude=52.0786, longitude=-1.01694),
            "Monza": CircuitLocation(name="Monza", latitude=45.6156, longitude=9.28111),
            "Spa": CircuitLocation(name="Spa", latitude=50.4372, longitude=5.97139),
            "Suzuka": CircuitLocation(name="Suzuka", latitude=34.8431, longitude=136.5407),
            "Austin": CircuitLocation(name="Austin", latitude=30.1328, longitude=-97.6411),
            "Interlagos": CircuitLocation(name="Interlagos", latitude=-23.7036, longitude=-46.6997),
            # Add more circuits as needed
        }

    async def get_weather_forecast(self, circuit_key: str, race_datetime: datetime) -> Optional[WeatherData]:
        """Get weather forecast for a specific circuit and time"""
        try:
            circuit_location = self._get_circuit_location(circuit_key)
            if not circuit_location:
                logger.warning(f"Circuit location not found for {circuit_key}")
                return None

            if self.weather_provider == "openweathermap" and self.openweather_api_key:
                return await self._get_openweathermap_forecast(circuit_location, race_datetime)
            else:
                return await self._get_open_meteo_forecast(circuit_location, race_datetime)
        except Exception as e:
            logger.error(f"Error getting weather forecast: {e}")
            return None

    async def get_current_weather(self, circuit_key: str) -> Optional[WeatherData]:
        """Get current weather for a circuit"""
        try:
            circuit_location = self._get_circuit_location(circuit_key)
            if not circuit_location:
                return None

            if self.weather_provider == "openweathermap" and self.openweather_api_key:
                return await self._get_openweathermap_current(circuit_location)
            else:
                return await self._get_open_meteo_current(circuit_location)
        except Exception as e:
            logger.error(f"Error getting current weather: {e}")
            return None

    async def get_weather_history(self, circuit_key: str, start_date: datetime, end_date: datetime) -> List[WeatherData]:
        """Get historical weather data"""
        try:
            circuit_location = self._get_circuit_location(circuit_key)
            if not circuit_location:
                return []

            # For now, use Open-Meteo for historical data as it's free
            return await self._get_open_meteo_history(circuit_location, start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting weather history: {e}")
            return []

    async def _get_openweathermap_forecast(self, location: CircuitLocation, target_datetime: datetime) -> Optional[WeatherData]:
        """Get forecast from OpenWeatherMap API"""
        try:
            url = "http://api.openweathermap.org/data/2.5/forecast"
            params = {
                "lat": location.latitude,
                "lon": location.longitude,
                "appid": self.openweather_api_key,
                "units": "metric"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                # Find the forecast closest to target time
                target_timestamp = target_datetime.strftime("%Y-%m-%d %H:%M:%S")
                closest_forecast = None
                min_time_diff = float('inf')

                for forecast in data["list"]:
                    forecast_time = forecast["dt_txt"]
                    time_diff = abs((datetime.strptime(forecast_time, "%Y-%m-%d %H:%M:%S") - target_datetime).total_seconds())
                    
                    if time_diff < min_time_diff:
                        min_time_diff = time_diff
                        closest_forecast = forecast

                if closest_forecast:
                    return self._parse_openweathermap_data(closest_forecast)

        except Exception as e:
            logger.error(f"OpenWeatherMap API error: {e}")
            return None

    async def _get_openweathermap_current(self, location: CircuitLocation) -> Optional[WeatherData]:
        """Get current weather from OpenWeatherMap"""
        try:
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": location.latitude,
                "lon": location.longitude,
                "appid": self.openweather_api_key,
                "units": "metric"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                return WeatherData(
                    timestamp=datetime.now(),
                    temperature_c=data["main"]["temp"],
                    wind_kph=data["wind"]["speed"] * 3.6,  # Convert m/s to km/h
                    precipitation_prob=0.0,  # Current weather doesn't include probability
                    precipitation_mm=data.get("rain", {}).get("1h", 0.0),
                    cloud_percentage=data["clouds"]["all"],
                    humidity_percentage=data["main"]["humidity"],
                    pressure_hpa=data["main"]["pressure"],
                    weather_condition=data["weather"][0]["description"],
                    is_wet=data.get("rain", {}).get("1h", 0) > 0.1
                )

        except Exception as e:
            logger.error(f"OpenWeatherMap current weather error: {e}")
            return None

    async def _get_open_meteo_forecast(self, location: CircuitLocation, target_datetime: datetime) -> Optional[WeatherData]:
        """Get forecast from Open-Meteo (free alternative)"""
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "hourly": "temperature_2m,precipitation_probability,precipitation,windspeed_10m,cloudcover,relativehumidity_2m,surface_pressure",
                "timezone": "auto",
                "forecast_days": 7
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                # Find closest time index
                hourly = data["hourly"]
                target_time_str = target_datetime.strftime("%Y-%m-%dT%H:00")
                
                if target_time_str in hourly["time"]:
                    index = hourly["time"].index(target_time_str)
                    
                    precip_mm = hourly["precipitation"][index] or 0.0
                    
                    return WeatherData(
                        timestamp=target_datetime,
                        temperature_c=hourly["temperature_2m"][index],
                        wind_kph=hourly["windspeed_10m"][index],
                        precipitation_prob=hourly["precipitation_probability"][index] / 100.0,
                        precipitation_mm=precip_mm,
                        cloud_percentage=hourly["cloudcover"][index],
                        humidity_percentage=hourly["relativehumidity_2m"][index],
                        pressure_hpa=hourly["surface_pressure"][index],
                        weather_condition=self._get_weather_condition(precip_mm, hourly["cloudcover"][index]),
                        is_wet=precip_mm > 0.1
                    )

        except Exception as e:
            logger.error(f"Open-Meteo forecast error: {e}")
            return None

    async def _get_open_meteo_current(self, location: CircuitLocation) -> Optional[WeatherData]:
        """Get current weather from Open-Meteo"""
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "current": "temperature_2m,precipitation,windspeed_10m,cloudcover,relativehumidity_2m,surface_pressure",
                "timezone": "auto"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                current = data["current"]
                precip_mm = current["precipitation"] or 0.0

                return WeatherData(
                    timestamp=datetime.now(),
                    temperature_c=current["temperature_2m"],
                    wind_kph=current["windspeed_10m"],
                    precipitation_prob=0.0,  # Current data doesn't include probability
                    precipitation_mm=precip_mm,
                    cloud_percentage=current["cloudcover"],
                    humidity_percentage=current["relativehumidity_2m"],
                    pressure_hpa=current["surface_pressure"],
                    weather_condition=self._get_weather_condition(precip_mm, current["cloudcover"]),
                    is_wet=precip_mm > 0.1
                )

        except Exception as e:
            logger.error(f"Open-Meteo current weather error: {e}")
            return None

    async def _get_open_meteo_history(self, location: CircuitLocation, start_date: datetime, end_date: datetime) -> List[WeatherData]:
        """Get historical weather from Open-Meteo"""
        try:
            url = "https://archive-api.open-meteo.com/v1/archive"
            params = {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "hourly": "temperature_2m,precipitation,windspeed_10m,cloudcover,relativehumidity_2m,surface_pressure",
                "timezone": "auto"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                weather_history = []
                hourly = data["hourly"]
                
                for i in range(len(hourly["time"])):
                    precip_mm = hourly["precipitation"][i] or 0.0
                    
                    weather_point = WeatherData(
                        timestamp=datetime.fromisoformat(hourly["time"][i]),
                        temperature_c=hourly["temperature_2m"][i],
                        wind_kph=hourly["windspeed_10m"][i],
                        precipitation_prob=0.0,  # Historical data doesn't include probability
                        precipitation_mm=precip_mm,
                        cloud_percentage=hourly["cloudcover"][i],
                        humidity_percentage=hourly["relativehumidity_2m"][i],
                        pressure_hpa=hourly["surface_pressure"][i],
                        weather_condition=self._get_weather_condition(precip_mm, hourly["cloudcover"][i]),
                        is_wet=precip_mm > 0.1
                    )
                    weather_history.append(weather_point)

                return weather_history

        except Exception as e:
            logger.error(f"Open-Meteo history error: {e}")
            return []

    def _get_circuit_location(self, circuit_key: str) -> Optional[CircuitLocation]:
        """Get circuit location by key"""
        # Convert circuit_key to a more readable format for lookup
        circuit_name = circuit_key.replace("_", " ").title()
        
        # Try direct lookup first
        if circuit_name in self.circuit_locations:
            return self.circuit_locations[circuit_name]
        
        # Try some common mappings
        mapping = {
            "albert_park": "Albert Park",
            "red_bull_ring": "Red Bull Ring",
            "yas_marina": "Abu Dhabi",
            "cota": "Austin"
        }
        
        if circuit_key in mapping:
            mapped_name = mapping[circuit_key]
            if mapped_name in self.circuit_locations:
                return self.circuit_locations[mapped_name]
        
        return None

    def _parse_openweathermap_data(self, forecast_data: Dict) -> WeatherData:
        """Parse OpenWeatherMap forecast data"""
        precip_mm = forecast_data.get("rain", {}).get("3h", 0.0)
        
        return WeatherData(
            timestamp=datetime.fromtimestamp(forecast_data["dt"]),
            temperature_c=forecast_data["main"]["temp"],
            wind_kph=forecast_data["wind"]["speed"] * 3.6,
            precipitation_prob=forecast_data.get("pop", 0.0),
            precipitation_mm=precip_mm,
            cloud_percentage=forecast_data["clouds"]["all"],
            humidity_percentage=forecast_data["main"]["humidity"],
            pressure_hpa=forecast_data["main"]["pressure"],
            weather_condition=forecast_data["weather"][0]["description"],
            is_wet=precip_mm > 0.1
        )

    def _get_weather_condition(self, precipitation_mm: float, cloud_cover: int) -> str:
        """Determine weather condition from precipitation and cloud cover"""
        if precipitation_mm > 5.0:
            return "heavy rain"
        elif precipitation_mm > 1.0:
            return "light rain"
        elif precipitation_mm > 0.1:
            return "drizzle"
        elif cloud_cover > 80:
            return "overcast"
        elif cloud_cover > 50:
            return "partly cloudy"
        else:
            return "clear"

    def calculate_weather_impact(self, weather_data: WeatherData, circuit_key: str) -> Dict[str, float]:
        """
        Calculate weather impact on race performance
        Based on your sample's weather effects logic
        """
        impact = {
            "temperature_effect": 1.0,
            "rain_effect": 1.0,
            "wind_effect": 1.0,
            "track_wet": weather_data.is_wet,
            "chaos_multiplier": 1.0
        }

        # Temperature effects (from your config)
        if weather_data.temperature_c > 30:
            impact["temperature_effect"] = 0.95  # Hot conditions
        elif weather_data.temperature_c < 15:
            impact["temperature_effect"] = 0.98  # Cold conditions
        else:
            impact["temperature_effect"] = 1.0   # Optimal conditions

        # Rain effects
        if weather_data.precipitation_mm > 5.0:
            impact["rain_effect"] = 0.85  # Heavy rain - significant impact
            impact["chaos_multiplier"] = 2.0
        elif weather_data.precipitation_mm > 1.0:
            impact["rain_effect"] = 0.92  # Light rain
            impact["chaos_multiplier"] = 1.3
        elif weather_data.precipitation_mm > 0.1:
            impact["rain_effect"] = 0.97  # Drizzle
            impact["chaos_multiplier"] = 1.1

        # Wind effects
        if weather_data.wind_kph > 25:
            impact["wind_effect"] = 0.98  # High wind penalty

        return impact

# Service instance
weather_service = WeatherService()