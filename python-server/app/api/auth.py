"""Auth API endpoints and Dependencies"""
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.services.auth_service import AuthService
from app.schemas.response import StandardResponse

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# --- Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    username: str
    id: str

# --- Dependencies ---
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Dependency to get the currently authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = AuthService.decode_token(token)
    if payload is None:
        raise credentials_exception
        
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# --- Routes ---

@router.post("/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new local user (usually call once on first setup)"""
    # Check if exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        return StandardResponse(code=1, status="error", data={"error": "Username already exists"})
    
    # Create user
    new_user = User(
        id=str(uuid.uuid4()),
        username=user_data.username,
        hashed_password=AuthService.get_password_hash(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return StandardResponse(code=0, status="success", data={"username": new_user.username})

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 compatible token login"""
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not AuthService.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = AuthService.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return StandardResponse(code=0, status="success", data={
        "username": current_user.username,
        "id": current_user.id
    })
