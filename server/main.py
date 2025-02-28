import uuid
import uvicorn
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from fastapi import FastAPI, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse

from payments import create_payment_information, webhook, PaymentContextStore
from weather_api import WeatherAPI
from users import User, UserStore, get_current_user

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Weather API")
weather_api = WeatherAPI()


class UserResponse(BaseModel):
    user_id: str = Field(..., description="The user's UUID token")
    credits: int = Field(..., description="Number of credits available")

@app.post("/signup", response_model=UserResponse)
def create_user():
    """Create a new user and return their UUID token"""
    user_id = str(uuid.uuid4())
    credits = 1
    UserStore[user_id] = User(user_id=user_id, credits=credits)
    return {"user_id": user_id, "credits": credits}


@app.get("/user", response_model=UserResponse)
def get_user_info(current_user: User = Depends(get_current_user)):
    """Get information about the current user"""
    if current_user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {"user_id": current_user.user_id, "credits": current_user.credits}


class WeatherResponse(BaseModel):
    temperature: float = Field(..., description="Current temperature in Celsius")
    condition: str = Field(..., description="Weather condition (e.g., sunny, cloudy)")
    location: str = Field(..., description="Location name and country")
    humidity: int = Field(..., description="Humidity percentage")
    wind_kph: float = Field(..., description="Wind speed in kilometers per hour")
    feels_like: float = Field(..., description="Feels like temperature in Celsius")
    last_updated: str = Field(..., description="Time when weather data was last updated")
    
@app.get("/weather", response_model=WeatherResponse)
async def get_weather(
    current_user: User = Depends(get_current_user),
    location: str = Query("San Francisco", description="City name or coordinates")
):
    """
    Get current weather information for a location.
    Default location is San Francisco if not specified.
    Requires authentication and consumes one credit.
    """
    if current_user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    if current_user.credits <= 0:
        response = create_payment_information(current_user.user_id)    
        return JSONResponse(status_code=402, content=response.json())
    
    try:
        # Deduct a credit
        UserStore[current_user.user_id].credits -= 1
        
        # Get weather data from the API
        weather_data = await weather_api.get_current_weather(location)
        return weather_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Refund the credit since the request failed
        UserStore[current_user.user_id].credits += 1
        raise HTTPException(status_code=500, detail=f"Failed to get weather data: {str(e)}")


class PaymentWebhookPayload(BaseModel):
    offer_id: str = Field(..., description="ID of the offer that was paid")
    payment_context_token: str = Field(..., description="Payment context token")
    amount: int = Field(..., description="Payment amount in cents")
    currency: str = Field(..., description="Payment currency")
    status: str = Field(..., description="Payment status")
    timestamp: str = Field(..., description="Payment timestamp")


@app.post("/webhook/fewsats")
async def fewsats_webhook(payload: PaymentWebhookPayload = Body(...)):
    """
    Webhook endpoint for Fewsats payment notifications.
    Updates user credits based on the payment information.
    """
    return webhook(payload)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
