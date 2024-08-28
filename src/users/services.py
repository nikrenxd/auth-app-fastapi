import jwt
from datetime import datetime, timedelta

from fastapi import HTTPException, status

from src.settings import settings
from src.users.dao import UserDAO, RefreshTokenDAO
from src.users.security import create_token, verify_password

# TODO Refactor UserService and RefreshTokenService(SecurityService)


class UserService:
    @classmethod
    async def get_user(cls, **filters):
        return await UserDAO.get_one(**filters)

    @classmethod
    async def create_user(cls, **data):
        await UserDAO.add(**data)

    @classmethod
    async def authenticate_user(cls, user_email: str, user_password: str):
        user = await cls.get_user(email=user_email)
        if not user and verify_password(user_password, user.password):
            return False

        return user


class RefreshTokenService:
    @classmethod
    async def logout(cls, refresh_token: str):
        token = await RefreshTokenDAO.get_one(refresh_token=refresh_token)
        if token:
            await RefreshTokenDAO.delete(refresh_token=refresh_token)

    @classmethod
    async def create_refresh_token(
        cls, data: dict, token_secret: str, expire_days: int
    ) -> str:
        to_encode = data.copy()
        token_expires = datetime.utcnow() + timedelta(days=expire_days)
        to_encode.update({"exp": token_expires})

        refresh_token = jwt.encode(
            to_encode,
            token_secret,
            algorithm=settings.JWT_ALGORITHM,
        )

        await RefreshTokenDAO.add(
            refresh_token=refresh_token,
            user_id=to_encode.get("sub"),
            expires_in=token_expires,
        )

        return refresh_token

    @classmethod
    async def refresh(cls, token: str):
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
        user = await UserService.get_user(id=refresh_token.user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        access_token = create_token(
            {"sub": user.id},
            settings.JWT_ACCESS_SECRET,
            settings.JWT_ACCESS_EXPIRE,
        )

        # Creating refresh token
        to_encode = {"sub": user.id}
        token_expires = datetime.utcnow() + timedelta(
            seconds=settings.JWT_REFRESH_EXPIRE
        )
        to_encode.update({"exp": token_expires})

        new_refresh_token = jwt.encode(
            to_encode, settings.JWT_REFRESH_SECRET, algorithm="HS256"
        )

        r_token = await RefreshTokenDAO.update(
            {"refresh_token": new_refresh_token, "expires_in": token_expires},
            id=refresh_token.id,
        )

        return {"access_token": access_token, "refresh_token": r_token.refresh_token}
