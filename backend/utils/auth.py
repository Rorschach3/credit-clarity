from typing import Optional, Dict
import uuid
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta

security = HTTPBearer()

class RateLimiter:
    def __init__(self, max_requests: int, window_minutes: int):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.client_requests: Dict[str, List[datetime]] = {}

    def allow_request(self, client_id: str) -> bool:
        now = datetime.now()
        if client_id not in self.client_requests:
            self.client_requests[client_id] = []

        # Remove old requests outside the window
        self.client_requests[client_id] = [
            req_time for req_time in self.client_requests[client_id]
            if now - req_time < timedelta(minutes=self.window_minutes)
        ]

        if len(self.client_requests[client_id]) < self.max_requests:
            self.client_requests[client_id].append(now)
            return True
        return False

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[uuid.UUID]:
    """
    Extract user ID from JWT token
    Replace this with your actual authentication logic
    """
    try:
        # TODO: Implement actual JWT token validation
        # For now, returning None to allow anonymous uploads
        return None
        
        # Example implementation:
        # token = credentials.credentials
        # payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # user_id = payload.get("sub")
        # return uuid.UUID(user_id) if user_id else None
        
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def get_current_user(user_id: Optional[uuid.UUID] = Depends(get_current_user_id)) -> Dict:
    """
    Placeholder for fetching user details.
    In a real app, this would fetch user data from a database.
    """
    if user_id is None:
        # For now, allow anonymous access for simplicity in development
        return {"user_id": "anonymous", "role": "guest"}
    
    # Mock user data for demonstration
    if str(user_id) == "some-admin-uuid": # Replace with actual admin UUID
        return {"user_id": str(user_id), "role": "admin"}
    
    return {"user_id": str(user_id), "role": "user"}