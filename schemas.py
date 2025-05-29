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

class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    timestamp: datetime

    class Config:
        orm_mode = True

class CreateChatRequest(BaseModel):
    partner_id: int

class ChatSessionResponse(BaseModel):
    id: int
    partnerId: int
    partnerName: str
    partnerAvatar: str
    lastMessage: str | None
    lastMessageTime: datetime
    unreadCount: int
