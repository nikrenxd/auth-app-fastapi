from datetime import timedelta, datetime

import jwt
from passlib.context import CryptContext

from src.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _tokens_expiration(access_expiration: int, refresh_expiration: int):
    return timedelta(minutes=access_expiration), timedelta(days=refresh_expiration)


def _token_expire_in(expire_time: timedelta):
    return datetime.utcnow() + expire_time


class TokensCreation:
    @classmethod
    def _create_token(
        cls, data: dict, token_secret: str, expire_time: timedelta
    ) -> str:
        to_encode = data.copy()
        expire = _token_expire_in(expire_time)
        to_encode.update({"exp": expire})

        token = jwt.encode(
            to_encode,
            token_secret,
            algorithm=settings.JWT_ALGORITHM,
        )

        return token

    @classmethod
    async def _create_refresh_token(
        cls,
        data: dict,
        token_secret: str,
        token_expires: timedelta,
    ) -> str:
        token = cls._create_token(data, token_secret, token_expires)

        return token

    @classmethod
    async def get_tokens(
        cls,
        data: dict,
        access_expiration: timedelta,
        refresh_expiration: timedelta,
    ):
        access_token = cls._create_token(
            data,
            settings.JWT_ACCESS_SECRET,
            access_expiration,
        )
        refresh_token = await cls._create_refresh_token(
            data,
            settings.JWT_REFRESH_SECRET,
            refresh_expiration,
        )

        return {"access": access_token, "refresh": refresh_token}
