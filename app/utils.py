from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated='auto')

def hash_password(password):
    return pwd_context.hash(password)

async def verify_password(password, hashed_password):
    return pwd_context.verify(password, hashed_password)