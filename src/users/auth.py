from fastapi import HTTPException, status
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.settings import settings
from src.users.utils import (
    _tokens_expiration,
    _token_expire_in,
    TokensCreation,
    verify_password,
)
from src.users.services import RefreshTokenService, UserService


class Authentication:
    token_utils = TokensCreation

    @classmethod
    async def login(cls, session: AsyncSession, data: dict) -> dict[str, str]:
        access_token_expires, refresh_token_expires = _tokens_expiration(
            settings.JWT_ACCESS_EXPIRE,
            settings.JWT_REFRESH_EXPIRE,
        )
        tokens = await cls.token_utils.get_tokens(
            data, access_token_expires, refresh_token_expires
        )

        user_id = data.get("sub")
        refresh_token = tokens.get("refresh")
        token_expires = _token_expire_in(refresh_token_expires)

        await RefreshTokenService.add_refresh(
            session,
            token_expires,
            refresh_token,
            user_id,
        )

        return tokens

    @classmethod
    async def logout(cls, session: AsyncSession, refresh_token: str):
        token = await RefreshTokenService.get_one(session, refresh_token=refresh_token)
        if token:
            await RefreshTokenService.delete(session, refresh_token=refresh_token)

    @classmethod
    async def authenticate_user(
        cls,
        session: AsyncSession,
        user_email: str,
        user_password: str,
    ):
        user = await UserService.get_one(session, email=user_email)
        if not user and verify_password(user_password, user.password):
            return False

        return user

    @classmethod
    async def refresh(cls, session: AsyncSession, token: str):
        access_token_expires, refresh_token_expires = _tokens_expiration(
            settings.JWT_ACCESS_EXPIRE,
            settings.JWT_REFRESH_EXPIRE,
        )
        refresh_token = await RefreshTokenService.get_one(session, refresh_token=token)

        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        if refresh_token.expires_in.timestamp() <= datetime.utcnow().timestamp():
            await RefreshTokenService.delete(session, id=refresh_token.id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
            )

        user = await UserService.get_one(session, id=refresh_token.user_id)
        data = {"sub": user.id}

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        tokens = await cls.token_utils.get_tokens(
            data,
            access_token_expires,
            refresh_token_expires,
        )

        new_refresh_token = await RefreshTokenService.update(
            session,
            {
                "refresh_token": tokens.pop("refresh"),
                "expires_in": _token_expire_in(refresh_token_expires),
            },
            id=refresh_token.id,
        )
        tokens.update(refresh=new_refresh_token.refresh_token)

        return tokens
