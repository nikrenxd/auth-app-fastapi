from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Response, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession


from src.database import get_session
from src.users.schemas import SUserCreate
from src.users.services import UserService
from src.users.utils import hash_password
from src.users.auth import Authentication

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/register")
async def user_register(
    body: SUserCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    user = await UserService.get_one(session, email=body.email)

    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email, already exists",
        )

    hashed_password = hash_password(body.password)

    await UserService.add(
        session,
        email=body.email,
        password=hashed_password,
    )


@router.post("/login")
async def user_login(
    request: Request,
    response: Response,
    body: SUserCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    user = await Authentication.authenticate_user(session, body.email, body.password)

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
    data = {"sub": user.id}
    tokens = await Authentication.login(session, data)

    response.set_cookie("access_token", tokens.get("access"), httponly=True)
    response.set_cookie("refresh_token", tokens.get("refresh"), httponly=True)

    return tokens


@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    new_tokens = await Authentication.refresh(
        session, request.cookies.get("refresh_token")
    )

    response.set_cookie("access_token", new_tokens.get("access"), httponly=True)
    response.set_cookie("refresh_token", new_tokens.get("refresh"), httponly=True)

    return new_tokens


@router.post("/logout")
async def user_logout(
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    await Authentication.logout(session, request.cookies.get("refresh_token"))
