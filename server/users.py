from typing import Dict, Optional
from fastapi import Header

# In-memory user storage
class User:
    def __init__(self, user_id: str, credits: int = 1):
        self.user_id = user_id
        self.credits = credits

# Store users by their UUID token
UserStore: Dict[str, User] = {}

# Authentication dependency
def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[User]:
    if not authorization:
        return None

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    token = parts[1]
    if token not in UserStore:
        return None
    
    return UserStore[token]

