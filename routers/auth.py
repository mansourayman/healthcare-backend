# backend/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import schema
import models 
from security.jwt import (
    ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY, create_access_token
)
from security.passwordFunc import encryptPassword, checkPassword
from datetime import datetime, timedelta
from database import sessionLocal
from sqlalchemy.orm import Session
from jose import JWTError, jwt

router = APIRouter(prefix="/auth", tags=["auth"])

def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- REGISTER ----------
@router.post("/register", response_model=schema.UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user: schema.UserCreate, db: Session = Depends(get_db)):
    existUser = db.query(models.User).filter(models.User.email == user.email).first()
    if existUser:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    hashed_password = encryptPassword(user.password)

    new_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,  # must match column name
        dob=user.dob,
        gender=user.gender,
        created_at=datetime.utcnow(),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# ---------- LOGIN ----------
@router.post("/login", response_model=schema.TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not checkPassword(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    user.last_login = datetime.utcnow()
    db.add(user)
    db.commit()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "id": user.id},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ---------- ME ----------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

@router.get("/me", response_model=schema.UserRead)
def get_logged_user(current_user: models.User = Depends(get_current_user)):
    return current_user
