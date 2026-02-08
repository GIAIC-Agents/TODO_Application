from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import Dict
from ..database import engine
from ..models.user import User, UserCreate, UserPublic
from ..services.auth_service import authenticate_user, create_user, get_user_by_email
from ..api.middleware.auth_middleware import JWTBearer
from ..services.auth_service import create_access_token
from datetime import timedelta

router = APIRouter()


def get_session():
    with Session(engine) as session:
        yield session


@router.post("/register")
def register(user: UserCreate, session: Session = Depends(get_session)):
    # Check if user already exists
    existing_user = get_user_by_email(session, email=user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    db_user = create_user(session, user)
    
    # Create access token for the new user
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": str(db_user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login")
def login(user: UserCreate, session: Session = Depends(get_session)):
    db_user = authenticate_user(session, user.email, user.password)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=30)  # Use the value from settings
    access_token = create_access_token(
        data={"sub": str(db_user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}