import os
from typing import Dict

from fewsats.core import *
from users import UserStore

# Store payment context tokens mapped to user IDs
PaymentContextStore: Dict[str, str] = {}

fewsats_api_key = os.getenv("FEWSATS_API_KEY")
if not fewsats_api_key:
    raise ValueError("FEWSATS_API_KEY is not set")

fs = Fewsats(api_key=fewsats_api_key)

offers = [
        {
            "offer_id": "offer_1",
            "title": "1 credit package",
            "description": "Add 1 credit to your account.",
            "amount": 1, # Price in USD Cents
            "currency": "USD", 
            "payment_methods": ["lightning"] # Each offer can support different payment methods
        },
        {
            "offer_id": "offer_2",
            "title": "1000 credit package",
            "description": "Add 1000 credits to your account.",
            "amount": 500, # Price in USD Cents
            "currency": "USD",
            "payment_methods": ["lightning", "credit_card"] # One offer can support multiple payment methods
        },
    ]

def create_payment_information(current_user_id):
    """
    Create L402 response for the available offers
    """
    # Create the L402 response body with infomation about the offers and how to pay
    offers_information = fs.create_offers(offers)
    offers_information.raise_for_status()

    # Store the payment context token with the user ID
    # So we can credit the user when they pay (we will receive a webhook from Fewsats)
    payment_context_token = offers_information.json().get("payment_context_token")
    PaymentContextStore[payment_context_token] = current_user_id
    
    return offers_information

def webhook(payload):
    """
    Webhook for Fewsats payment events
    """
    # Verify payment status
    if payload.status != "completed":
        return {"status": "error", "message": f"Payment status is {payload.status}, not completed"}
    
    # Get the user ID associated with this payment context token
    user_id = PaymentContextStore.get(payload.payment_context_token)
    if not user_id:
        return {"status": "error", "message": "Payment context token not found"}
    
    # Get the user
    user = UserStore.get(user_id)
    if not user:
        return {"status": "error", "message": "User not found"}
    
    # Add credits based on the offer ID
    if payload.offer_id == "offer_1":
        user.credits += 1
    elif payload.offer_id == "offer_2":
        user.credits += 1000
    else:
        return {"status": "error", "message": f"Unknown offer ID: {payload.offer_id}"}
    
    # Clean up the payment context token
    PaymentContextStore.pop(payload.payment_context_token, None)
    
    return {"status": "success", "user_id": user_id, "credits": user.credits}
