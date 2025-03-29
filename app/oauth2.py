from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import PyJWTError
import requests
from config import settings
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import models, database
from sqlmodel import select

GOOGLE_JWKS_URL = settings.google_jwks_url
GOOGLE_ISSUER = settings.google_issuer
CLIENT_ID = settings.client_id

oauth_schema = OAuth2PasswordBearer(tokenUrl="login")

async def get_jwks():
    response = await requests.get(GOOGLE_JWKS_URL)
    response.raise_for_status()
    return response.json()

async def verify_jwt(token: str, credentials_exception):
    try:
        jwks = await get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise PyJWTError("No kid in token header")
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise PyJWTError("No matching key found")
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=GOOGLE_ISSUER,
            audience=CLIENT_ID
        )
        return payload
    except PyJWTError as e:
        raise credentials_exception
    
async def get_current_user(token: str = Depends(oauth_schema), session: AsyncSession = Depends(database.get_session)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="could not authorize", headers={"WWW-Authenticate": "Bearer"},)
    
    payload = await verify_jwt(token, credentials_exception)
    oauth_id = payload.get("sub")
    if not oauth_id:
        raise credentials_exception
    user = (await session.execute(select(models.User).where(models.User.oauth_id == oauth_id))).scalar_one_or_none()
    if user is None:
        user = models.User(
            oauth_id=oauth_id,
            username=payload.get("name"),
            email=payload.get("email")
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


