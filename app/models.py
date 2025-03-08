from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON
from pydantic import EmailStr
from typing import Optional, List, Annotated
from datetime import datetime
import uuid

class UserBase(SQLModel):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    email: EmailStr = Field(unique=True, index=True)
    password: str = Field()
    

class UserCreate(UserBase):
    wallet_address: Optional[Annotated[str, Field(regex=r"^0x[0-9a-fA-F]{64}$")]] = None

class UserLogin(SQLModel):
    email: EmailStr
    password: str

class Users(UserBase, table=True, extend_existing=True):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    wallet_address: Optional[str] = Field()
    tokens: List["Tokens"] = Relationship(back_populates="user", cascade_delete=True)

class UserPublic(SQLModel):
    id: uuid.UUID 
    email: EmailStr

    class Config:
        from_attributes = True

class Events(SQLModel, table=True, extend_existing=True):
    id:  Optional[int] = Field(default=None, primary_key=True)
    organizer: str = Field(index=True,foreign_key="users.email", ondelete="CASCADE")
    location: str = Field()
    event_name: str = Field()
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    max_tokens: int = Field()
    upload_id: str = Field(unique=True)
    artwork_attributes: dict = Field(sa_column=Column(JSON))
    tokens: List["Tokens"] = Relationship(back_populates="events")


class EventCreate(SQLModel):
    organizer: str
    location: str
    max_tokens: int

class Tokens(SQLModel, table=True, extend_existing=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    event_id: int = Field(foreign_key="events.id", ondelete="CASCADE")
    metadata_cid: str
    claimed_at: datetime = Field(default_factory=datetime.utcnow)
    user: "Users" = Relationship(back_populates="tokens")
    events: "Events" = Relationship(back_populates="tokens")


class jwt_token(SQLModel):
    access_token: str
    type: str

class jwt_data(SQLModel):
    id: uuid.UUID