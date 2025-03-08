from fastapi import APIRouter, Depends,HTTPException, Response, status
from .. import models, oauth, database, utils
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
import asyncio
from .. import email, oauth


router = APIRouter(tags=['User'], prefix="/users")

@router.post("/", response_model=models.UserPublic, status_code=status.HTTP_201_CREATED)
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
        await email.send_email(user.email, user.name)
        return new_user
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    
@router.get("/", response_model=list[models.UserPublic])
async def get_users(current_user = Depends(oauth.get_current_user), session: AsyncSession = Depends(database.get_session)):
    users = await session.execute(select(models.Users))
    users = users.scalars().all()
    if users is None:
        return None
    return users


@router.delete("/")
async def delete_user(session: AsyncSession= Depends(database.get_session), current_user = Depends(oauth.get_current_user)):
    db_record = (await session.execute(select(models.Users).where(models.Users.id == current_user.id))).scalars().first()

    # if not db_record:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="T")

    await session.delete(db_record)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    