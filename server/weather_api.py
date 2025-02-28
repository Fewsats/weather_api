import os
import httpx
from typing import Dict, Any, Optional

class WeatherAPI:
    """Client for interacting with weatherapi.com"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("WEATHER_API_KEY")
        self.is_placeholder = not bool(self.api_key)
        self.base_url = "https://api.weatherapi.com/v1"
    
    async def get_current_weather(self, location: str = "San Francisco") -> Dict[str, Any]:
        """
        Get current weather information for a location
        
        Args:
            location: City name or coordinates (default: San Francisco)
            
        Returns:
            Dictionary containing weather information
        """
        if self.is_placeholder:
            return {
                "temperature": 21.0,
                "condition": "Placeholder weather data",
                "location": f"{location}, Placeholder Country",
                "humidity": 65,
                "wind_kph": 10.5,
                "feels_like": 20.0,
                "last_updated": "2023-01-01 12:00",
                "is_placeholder": True
            }
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/current.json",
                    params={
                        "key": self.api_key,
                        "q": location,
                        "aqi": "no"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract relevant information
                return {
                    "temperature": data["current"]["temp_c"],
                    "condition": data["current"]["condition"]["text"],
                    "location": f"{data['location']['name']}, {data['location']['country']}",
                    "humidity": data["current"]["humidity"],
                    "wind_kph": data["current"]["wind_kph"],
                    "feels_like": data["current"]["feelslike_c"],
                    "last_updated": data["current"]["last_updated"],
                    "is_placeholder": False
                }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                raise ValueError(f"Invalid location: {location}")
            elif e.response.status_code == 401:
                raise ValueError("Invalid API key")
            elif e.response.status_code == 403:
                raise ValueError("API key has exceeded its rate limit")
            else:
                raise ValueError(f"Weather API error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to get weather data: {str(e)}")
