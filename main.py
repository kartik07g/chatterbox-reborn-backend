# main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from models import User, Message
from schemas import UserCreate, MessageCreate, UserLogin
from crud import create_user, get_user_by_email, create_message, get_messages_between_users, verify_password

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return create_user(db=db, user=user)

@app.post("/messages/")
def send_message(message: MessageCreate, db: Session = Depends(get_db)):
    return create_message(db=db, message=message)

@app.get("/messages/{user_id}/{peer_id}")
def get_messages(user_id: int, peer_id: int, db: Session = Depends(get_db)):
    return get_messages_between_users(db=db, user_id=user_id, peer_id=peer_id)

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user.email)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    # return {"message": "Login successful", "user_id": db_user.id}
    return {
  "access_token": f"real-jwt-token-here{db_user.id}" ,
  "user": {
    "id": db_user.id,
    "fullname": db_user.fullname,
    "email": db_user.email,
    "avatar": ''
  }
}
