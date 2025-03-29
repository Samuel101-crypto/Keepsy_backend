from fastapi import Depends, HTTPException, status, APIRouter
from .. import database, models, utils, oauth
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from fastapi.security import OAuth2PasswordRequestForm
from .. import oauth2

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

@router.post("/register_address")
async def register_address(request: models.RegisterAddress, user = Depends(oauth2.get_current_user), session: AsyncSession = Depends(database.get_session)):
    # Check if address already exists for user
    existing_address = (await session.execute(select(models.Address).where(models.Address.address == request.address, models.Address.user_id == user.id))).scalar_one_or_none()
    if existing_address:
        raise HTTPException(status_code=400, detail="Address already registered for this user")
    new_address = models.Address(address=request.address, user_id=user.id)
    session.add(new_address)
    await session.commit()
    await session.refresh(new_address)
    return {"message": "Address registered successfully"}
