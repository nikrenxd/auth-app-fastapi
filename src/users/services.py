from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models import User, RefreshToken

from src.services import BaseService


class UserService(BaseService):
    model = User


class RefreshTokenService(BaseService):
    model = RefreshToken

    @classmethod
    async def add_refresh(
        cls,
        session: AsyncSession,
        expires: datetime,
        token: str,
        user_id: int,
    ):
        await super().add(
            session,
            refresh_token=token,
            user_id=user_id,
            expires_in=expires,
        )
