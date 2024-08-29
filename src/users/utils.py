from datetime import timedelta, datetime

from passlib.context import CryptContext

from src.users.dao import UserDAO

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def authenticate_user(user_email: str, user_password: str):
    user = await UserDAO.get_one(email=user_email)
    if not user and verify_password(user_password, user.password):
        return False

    return user


def _tokens_expiration(access_expiration: int, refresh_expiration: int):
    return timedelta(minutes=access_expiration), timedelta(days=refresh_expiration)


def _token_expire_in(expire_time: timedelta):
    return datetime.utcnow() + expire_time
