from pydantic import BaseModel, EmailStr, Field


class SignUpCommand(BaseModel):
    email: EmailStr = Field(examples=["proud@example.com"])
    name: str = Field(
        min_length=2, max_length=20, description="닉네임", examples=["프라우더"]
    )
    password: str = Field(min_length=8, max_length=64, examples=["Proud1234!"])


class UpdateProfileCommand(BaseModel):
    name: str = Field(min_length=2, max_length=20, description="닉네임")


class ChangePasswordCommand(BaseModel):
    old_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=64)
