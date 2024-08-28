from fastapi import APIRouter, HTTPException, status, Response, Request

from src.settings import settings
from src.users.schemas import SUserCreate
from src.users.services import UserService, RefreshTokenService
from src.users.security import (
    hash_password,
    create_token,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register")
async def user_register(body: SUserCreate):
    user = await UserService.get_user(email=body.email)

    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email, already exists",
        )

    hashed_password = hash_password(body.password)

    await UserService.create_user(email=body.email, password=hashed_password)


@router.post("/login")
async def user_login(request: Request, response: Response, body: SUserCreate):
    user = await UserService.authenticate_user(body.email, body.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if request.cookies.get("access_token") or request.cookies.get("refresh_token"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already logged in",
        )

    access_token = create_token(
        {"sub": user.id},
        settings.JWT_ACCESS_SECRET,
        settings.JWT_ACCESS_EXPIRE,
    )

    refresh_token = await RefreshTokenService.create_refresh_token(
        {"sub": user.id},
        settings.JWT_REFRESH_SECRET,
        settings.JWT_REFRESH_EXPIRE,
    )

    response.set_cookie("access_token", access_token, httponly=True)
    response.set_cookie("refresh_token", refresh_token, httponly=True)

    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/refresh")
async def refresh_token(request: Request, response: Response):
    new_tokens = await RefreshTokenService.refresh(request.cookies.get("refresh_token"))

    response.set_cookie("access_token", new_tokens.get("access_token"), httponly=True)
    response.set_cookie("refresh_token", new_tokens.get("refresh_token"), httponly=True)

    return new_tokens


@router.post("/logout")
async def user_logout(request: Request, response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    await RefreshTokenService.logout(request.cookies.get("refresh_token"))
