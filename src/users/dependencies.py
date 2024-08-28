# async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(
#             token,
#             settings.JWT_ACCESS_SECRET,
#             algorithms=[settings.JWT_ALGORITHM],
#         )
#         user_id: int = payload.get("sub")
#         if user_id is None:
#             raise credentials_exception
#     except InvalidTokenError:
#         raise credentials_exception
#
#     user = UserService.get_one(id=user_id)
#
#     if user is None:
#         raise credentials_exception
#
#     return user
