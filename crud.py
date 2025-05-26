from sqlalchemy.orm import Session
from models import User, Message
from schemas import UserCreate, MessageCreate
from passlib.context import CryptContext


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    db_user = User(fullname=user.fullname, email=user.email, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_message(db: Session, message: MessageCreate):
    db_message = Message(**message.dict())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_messages_between_users(db: Session, user_id: int, peer_id: int):
    return db.query(Message).filter(
        ((Message.sender_id == user_id) & (Message.receiver_id == peer_id)) |
        ((Message.sender_id == peer_id) & (Message.receiver_id == user_id))
    ).order_by(Message.timestamp).all()



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") 

def verify_password(plain_password, hashed_password):
    print("*****", plain_password, hashed_password)
    # return pwd_context.verify(plain_password, hashed_password)
    return plain_password == hashed_password

