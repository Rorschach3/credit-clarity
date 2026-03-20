from typing import Optional, Dict, List
import os
import uuid
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from supabase import create_client, Client

_supabase_url = os.getenv("SUPABASE_URL", "")
_supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")
supabase: Client = create_client(_supabase_url, _supabase_key) if _supabase_url and _supabase_key else None

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

async def get_current_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[uuid.UUID]:
    """
    Extract user ID from JWT token via Supabase server-side validation.
    Returns None if no credentials are provided (optional auth).
    Raises HTTPException(401) if credentials are invalid.
    """
    if credentials is None:
        return None

    if supabase is None:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")

    try:
        response = supabase.auth.get_user(credentials.credentials)
        user = response.user
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return uuid.UUID(user.id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def get_current_user(user_id: Optional[uuid.UUID] = Depends(get_current_user_id)) -> Dict:
    """
    Placeholder for fetching user details.
    In a real app, this would fetch user data from a database.
    """
    if user_id is None:
        # For now, allow anonymous access for simplicity in development
        return {"user_id": "anonymous", "role": "guest"}
    
    return {"user_id": str(user_id), "role": "user"}