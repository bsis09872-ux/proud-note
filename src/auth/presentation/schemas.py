from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str = Field(
        description="Authorization: Bearer <토큰> 으로 전달 (HS512)"
    )
    token_type: str = "bearer"
    expires_in: int = Field(description="유효 시간(초)", examples=[3600])
