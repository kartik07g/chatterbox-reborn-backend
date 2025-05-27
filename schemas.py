from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    fullname: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class MessageCreate(BaseModel):
    sender_id: int
    receiver_id: int
    content: str

class MessageOut(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    timestamp: datetime

    class Config:
        orm_mode = True

class ChatSessionResponse(BaseModel):
    partner_id: int
    partner_name: str
    last_message: str
    last_message_time: datetime

    class Config:
        orm_mode = True
