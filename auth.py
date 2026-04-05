import os
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client

bearer_scheme = HTTPBearer(auto_error=False)

def get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("Supabase env vars not set")
    return create_client(url, key)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    """
    Validates the JWT the frontend sends in the Authorization header.
    Returns the user dict or raises 401.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="No credentials provided")
        
    token = credentials.credentials
    supabase = get_supabase()
    try:
        response = supabase.auth.get_user(token)
        return response.user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
