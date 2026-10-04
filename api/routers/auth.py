import hashlib
import os
from fastapi import APIRouter, HTTPException, Response, Request
from pydantic import BaseModel
from api.database import get_db_connection

router = APIRouter(prefix="/api/auth", tags=["Auth"])

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
