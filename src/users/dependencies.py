from datetime import datetime

import jwt
from typing import Annotated

from fastapi import Request, HTTPException, status, Depends
from jwt import PyJWTError

from src.settings import settings
from src.users.dao import UserDAO


def get_token(request: Request) -> str:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            detail="Token is missing",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    return token


async def get_current_user(token: Annotated[get_token, Depends()]):
    try:
        data = jwt.decode(
            token, settings.JWT_ACCESS_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
    except PyJWTError:
        raise HTTPException(
            detail="Invalid token",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    expire = data.get("exp")
    if (not expire) and (int(expire) < datetime.utcnow().timestamp()):
        raise HTTPException(
            detail="Token expired",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    user_id = data.get("sub")
    if not user_id:
        raise HTTPException(
            detail="Invalid token",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    user = await UserDAO.get_one(id=user_id)
    if not user:
        raise HTTPException(
            detail="Invalid token",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    return user
