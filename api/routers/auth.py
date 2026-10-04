import hashlib
import os
import secrets
from fastapi import APIRouter, HTTPException, Response, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.config import Config
from api.database import get_db_connection

router = APIRouter(prefix="/api/auth", tags=["Auth"])

# OAuth setup
config = Config('.env')
oauth = OAuth(config)

oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

class LoginRequest(BaseModel):
    username: str
    password: str

def hash_password(password: str) -> str:
    salt = os.urandom(32)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ":" + pwd_hash.hex()

def verify_password(password: str, hashed_password: str) -> bool:
    try:
        salt_hex, pwd_hash_hex = hashed_password.split(':')
        salt = bytes.fromhex(salt_hex)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return pwd_hash.hex() == pwd_hash_hex
    except Exception:
        return False

@router.post("/login")
async def login(req: LoginRequest, response: Response):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (req.username,))
    user = cursor.fetchone()
    conn.close()

    if user and verify_password(req.password, user["password_hash"]):
        # Successful login, let's set a simple secure cookie for session
        response.set_cookie(key="session_token", value=req.username, httponly=True, max_age=3600)
        return {"status": "success", "message": "Login successful"}
    
    raise HTTPException(status_code=401, detail="Invalid username or password")

@router.get("/check")
async def check_auth(request: Request):
    if not request.cookies.get("session_token"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"status": "success", "username": request.cookies.get("session_token")}

@router.post("/register")
async def register(req: LoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (req.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_pwd = hash_password(req.password)
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (req.username, hashed_pwd))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail="Database error")
        
    conn.close()
    return {"status": "success", "message": "User registered successfully"}

@router.get("/login/google")
async def login_via_google(request: Request):
    # Port 8000 is used by default in crewairag
    redirect_uri = "http://localhost:8000/api/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def auth_google_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        userinfo = token.get('userinfo')
        if not userinfo:
            userinfo = await oauth.google.parse_id_token(request, token)
        
        email = userinfo.get('email')
        username = email.split('@')[0] if email else "google_user"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Auto-register if user doesn't exist
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if not user:
            pwd = secrets.token_urlsafe(16)
            hashed_pwd = hash_password(pwd)
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_pwd))
            conn.commit()
            
        conn.close()
        
        # Set session and redirect to dashboard
        response = RedirectResponse(url="/")
        response.set_cookie(key="session_token", value=username, httponly=True, max_age=3600*24*7)
        return response
        
    except OAuthError as error:
        return HTMLResponse(f"<h1>OAuth Error</h1><p>{error.error}</p>", status_code=400)
