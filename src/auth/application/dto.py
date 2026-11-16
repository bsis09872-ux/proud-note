from pydantic import BaseModel, EmailStr, Field


class LoginCommand(BaseModel):
    email: EmailStr = Field(examples=["proud@example.com"])
    password: str = Field(min_length=1, examples=["Proud1234!"])
