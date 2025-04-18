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

class RegisterAddress(SQLModel):
    address: Annotated[str, Field(regex=r"^0x[0-9a-fA-F]{64}$")]

class Users(SQLModel, table=True, extend_existing=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    oauth_id : str = Field(unique=True, index=True) #Column(String, unique=True, index=True, nullable=False)
    username: Optional[str] = Field() #Column(String, nullable=True)
    email : Optional[EmailStr] = Field() #Column(String, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tokens: List["Tokens"] = Relationship(back_populates="user", cascade_delete=True)
    addresses: List["Address"] = Relationship(back_populates="user")

class Address(SQLModel, table=True, extend_existing=True):
    id :int = Field(index=True, primary_key=True) #Column(Integer, primary_key=True, index=True)
    address: str = Field(unique=True)#Column(String, unique=True, nullable=False)
    user_id: uuid.UUID = Field(foreign_key="users.id") #Column(Integer, ForeignKey("users.id"))
    user: "Users" = Relationship(back_populates="addresses") #relationship("User", back_populates="addresses")



class UserPublic(SQLModel):
    id: uuid.UUID 
    email: EmailStr

    class Config:
        from_attributes = True

class Events(SQLModel, table=True, extend_existing=True):
    id:  Optional[int] = Field(default=None, primary_key=True)
    organizer: str = Field(index=True,foreign_key="users.id", ondelete="CASCADE") #created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    location: str = Field()
    event_name: str = Field()
    date_time: datetime = Field()
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    max_tokens: int = Field()
    nft_type: int = Field(default=0)
    nft_decription: str = Field()
    upload_id: str = Field(unique=True)
    artwork_attributes: dict = Field(sa_column=Column(JSON))
    tokens: List["Tokens"] = Relationship(back_populates="events")

class EventsPublic(SQLModel):
    id:  Optional[int] = Field(default=None, primary_key=True)
    organizer: str = Field(index=True,foreign_key="users.email", ondelete="CASCADE")
    location: str = Field()
    event_name: str = Field()
    date_time: datetime = Field()
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    max_tokens: int = Field()
    tokens: List["Tokens"] = Relationship(back_populates="events")

    class Config:
        # Pydantic v3: use from_attributes instead of orm_mode
        from_attributes = True

class UserProfile(SQLModel):
    user: UserPublic
    count: int
    events: List[EventsPublic]

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

class AttendeeCreate(SQLModel):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    email: EmailStr = Field(unique=True, index=True)
    