from pydantic import BaseModel, EmailStr


class SUserCreate(BaseModel):
    email: EmailStr
    password: str
