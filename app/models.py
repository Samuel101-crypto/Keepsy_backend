from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr
from typing import Optional, List
from datetime import datetime
import uuid

class UserBase(SQLModel):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    firstname: str
    email: EmailStr = Field(unique=True, index=True)
    password: str = Field()

class UserCreate(UserBase):
    pass

class Users(UserBase, table=True, extend_existing=True):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tokens: List["Token"] = Relationship(back_populates="user")

class UserPublic(SQLModel):
    id: uuid.UUID 
    email: EmailStr

class Event(SQLModel, table=True, extend_existing=True):
    id:  Optional[int] = Field(default=None, primary_key=True)
    organizer: str = Field(foreign_key="users.email")
    location: str
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    max_tokens: int
    tokens: List["Token"] = Relationship(back_populates="event")


class Token(SQLModel, table=True, extend_existing=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    event_id: int = Field(foreign_key="event.id")
    metadata_cid: str
    claimed_at: datetime = Field(default_factory=datetime.utcnow)
    user: "Users" = Relationship(back_populates="tokens")
    event: "Event" = Relationship(back_populates="tokens")