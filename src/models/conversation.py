from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List
from uuid import uuid4, UUID
import pytz

# Pakistan timezone
PKT = pytz.timezone('Asia/Karachi')

def get_pakistan_time():
    """Get current time in Pakistan timezone"""
    return datetime.now(PKT)


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"
    
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=get_pakistan_time)
    updated_at: datetime = Field(default_factory=get_pakistan_time)
    
    # Relationship
    messages: List["Message"] = Relationship(back_populates="conversation")


class Message(SQLModel, table=True):
    __tablename__ = "messages"
    
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="conversations.id", index=True)
    user_id: str = Field(index=True)
    role: str = Field()  # "user" or "assistant"
    content: str = Field()
    created_at: datetime = Field(default_factory=get_pakistan_time)
    
    # Relationship
    conversation: Optional[Conversation] = Relationship(back_populates="messages")
