from src.users.models import User, RefreshToken

from src.dao import BaseDAO


class UserDAO(BaseDAO):
    model = User


class RefreshTokenDAO(BaseDAO):
    model = RefreshToken
