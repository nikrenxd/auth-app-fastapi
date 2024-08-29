import jwt
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from src.settings import settings
from src.users.utils import _tokens_expiration, _token_expire_in
from src.users.dao import RefreshTokenDAO, UserDAO


class AuthenticationService:
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
    async def create_refresh_token(
        cls,
        data: dict,
        token_secret: str,
        token_expires: timedelta,
        refresh: bool = False,
    ) -> str:
        expire = _token_expire_in(token_expires)
        token = cls._create_token(data, token_secret, token_expires)
        user_id = data.get("sub")

        if not refresh:
            await RefreshTokenDAO.add(
                refresh_token=token,
                user_id=user_id,
                expires_in=expire,
            )

        return token

    @classmethod
    async def get_tokens(
        cls,
        data: dict,
        access_expiration: timedelta,
        refresh_expiration: timedelta,
        refresh: bool = False,
    ):
        access_token = cls._create_token(
            data,
            settings.JWT_ACCESS_SECRET,
            access_expiration,
        )
        refresh_token = await cls.create_refresh_token(
            data,
            settings.JWT_REFRESH_SECRET,
            refresh_expiration,
            refresh,
        )

        return {"access": access_token, "refresh": refresh_token}

    @classmethod
    async def login(cls, data: dict) -> dict[str, str]:
        access_token_expires, refresh_token_expires = _tokens_expiration(
            settings.JWT_ACCESS_EXPIRE,
            settings.JWT_REFRESH_EXPIRE,
        )
        tokens = await cls.get_tokens(data, access_token_expires, refresh_token_expires)

        return tokens

    @classmethod
    async def logout(cls, refresh_token: str):
        token = await RefreshTokenDAO.get_one(refresh_token=refresh_token)
        if token:
            await RefreshTokenDAO.delete(refresh_token=refresh_token)

    @classmethod
    async def refresh_tokens(cls, token: str):
        access_token_expires, refresh_token_expires = _tokens_expiration(
            settings.JWT_ACCESS_EXPIRE,
            settings.JWT_REFRESH_EXPIRE,
        )
        refresh_token = await RefreshTokenDAO.get_one(refresh_token=token)

        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        if refresh_token.expires_in.timestamp() <= datetime.utcnow().timestamp():
            await RefreshTokenDAO.delete(id=refresh_token.id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
            )

        user = await UserDAO.get_one(id=refresh_token.user_id)
        data = {"sub": user.id}

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        tokens = await cls.get_tokens(
            data,
            access_token_expires,
            refresh_token_expires,
            True,
        )

        new_refresh_token = await RefreshTokenDAO.update(
            {
                "refresh_token": tokens.pop("refresh"),
                "expires_in": _token_expire_in(refresh_token_expires),
            },
            id=refresh_token.id,
        )
        tokens.update(refresh=new_refresh_token.refresh_token)

        return tokens
