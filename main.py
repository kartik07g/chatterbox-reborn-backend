# main.py
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from models import User, Message, ChatSession
from schemas import UserCreate, MessageCreate, UserLogin, ChatSessionResponse
from crud import create_user, get_user_by_email, create_message, get_messages_between_users, verify_password
from fastapi import WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from fastapi import status
from typing import List
import random

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "your-secret-key"  # keep secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


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
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token = create_access_token(data={"user_id": db_user.id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "fullname": db_user.fullname,
            "email": db_user.email,
            "avatar": ""
        }
    }

@app.websocket("/ws/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Optionally store in DB here
            await manager.broadcast(f"User {user_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/chats/", response_model=list[ChatSessionResponse])
def get_chat_sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    messages = db.query(Message).filter(
        (Message.sender_id == user.id) | (Message.receiver_id == user.id)
    ).all()

    chat_partners = {}
    for msg in messages:
        partner_id = msg.receiver_id if msg.sender_id == user.id else msg.sender_id
        if partner_id not in chat_partners or msg.timestamp > chat_partners[partner_id]["last_message_time"]:
            chat_partners[partner_id] = {
                "last_message": msg.content,
                "last_message_time": msg.timestamp
            }

    chat_sessions = []
    for partner_id, info in chat_partners.items():
        partner = db.query(User).filter(User.id == partner_id).first()
        if partner:
            chat_sessions.append(ChatSessionResponse(
                user_id=partner.id,
                fullname=partner.fullname,
                email=partner.email,
                last_message=info["last_message"],
                last_message_time=info["last_message_time"]
            ))
    return chat_sessions


@app.post("/new_chats/", response_model=ChatSessionResponse)
def start_random_chat(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Get all other users
    other_users = db.query(User).filter(User.id != current_user.id).all()
    if not other_users:
        raise HTTPException(status_code=404, detail="No other users available")

    # Pick a random partner
    partner = random.choice(other_users)

    # Check for existing chat
    existing_chat = db.query(ChatSession).filter(
        ((ChatSession.user1_id == current_user.id) & (ChatSession.user2_id == partner.id)) |
        ((ChatSession.user1_id == partner.id) & (ChatSession.user2_id == current_user.id))
    ).first()

    if existing_chat:
        chat = existing_chat
    else:
        chat = ChatSession(user1_id=current_user.id, user2_id=partner.id)
        db.add(chat)
        db.commit()
        db.refresh(chat)

    return ChatSessionResponse(
        id=chat.id,
        partnerId=partner.id,
        partnerName=partner.fullname,
        partnerAvatar="",
        lastMessage="Start a conversation...",
        lastMessageTime=chat.created_at,
        unreadCount=0,
    )