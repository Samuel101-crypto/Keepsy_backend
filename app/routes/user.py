from fastapi import APIRouter, Depends,HTTPException, Response, status
from .. import models, oauth, database, utils
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
import asyncio


router = APIRouter(tags=['User'], prefix="/user")

@router.post("/")
async def create_user(user: models.UserCreate, session: AsyncSession = Depends(database.get_session)):
    try:
        db_record =  (await session.execute(select(models.Users).where(models.Users.email == user.email))).first()
        if db_record:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists!")
        hashed_password = await asyncio.to_thread(utils.hash_password, user.password)
        user.password = hashed_password
        new_user = models.Users(**user.model_dump())
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")