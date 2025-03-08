from fastapi import FastAPI, HTTPException, status, Depends
from . import models, database
from .database import engine
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession
from .routes import user, events, auth



app = FastAPI()

app.include_router(user.router)
app.include_router(events.router)
app.include_router(auth.router)

@app.on_event("startup")
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


@app.get("/")
async def root():
    return "Hello world!"
