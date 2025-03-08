from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from .. import database, models, utils, oauth
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(tags=["Auth"], prefix="/login")

@router.post("/")
async def login_user(user: OAuth2PasswordRequestForm= Depends(), session: AsyncSession = Depends(database.get_session)):
    db_record = await session.execute(select(models.Users).where(models.Users.email == user.username))
    db_record = db_record.scalar_one_or_none()

    if db_record == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")
    
    verified = await utils.verify_password(user.password, db_record.password)

    if not verified:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials")
    
    access_token = await oauth.create_jwt({"user_id": str(db_record.id)})

    return {"access_token" : access_token, "type": "Bearer"}