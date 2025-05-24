# main.py
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from models import User, Message
from schemas import UserCreate, MessageCreate
from crud import create_user, get_user_by_username, create_message, get_messages_between_users

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return create_user(db=db, user=user)

@app.post("/messages/")
def send_message(message: MessageCreate, db: Session = Depends(get_db)):
    return create_message(db=db, message=message)

@app.get("/messages/{user_id}/{peer_id}")
def get_messages(user_id: int, peer_id: int, db: Session = Depends(get_db)):
    return get_messages_between_users(db=db, user_id=user_id, peer_id=peer_id)
