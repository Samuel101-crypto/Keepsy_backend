
from datetime import datetime, timedelta
from . import models
import jwt
from jwt.exceptions import PyJWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from . database import get_session
from sqlmodel import Session
from . config import settings
import uuid


oauth_schema = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
EXPIRATION_TIME = int(settings.expiration_time)

async def create_jwt(data:dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=EXPIRATION_TIME)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

async def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        token_data = models.jwt_data(id=uuid.UUID(payload["user_id"]))

        if token_data.id is None:
            raise credentials_exception
    
    except PyJWTError:
        raise credentials_exception

    
    return token_data
    
async def get_current_user(token:str = Depends(oauth_schema), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="could not authorize", headers={"WWW-Authenticate": "Bearer"},)
    
    token = await verify_token(token, credentials_exception)

    user = await session.get(models.Users, token.id)

    return user