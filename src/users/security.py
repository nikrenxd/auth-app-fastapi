import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

from src.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(data: dict, token_secret: str, expire_time: int) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expire_time)
    to_encode.update({"exp": expire})

    token = jwt.encode(
        to_encode,
        token_secret,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token
