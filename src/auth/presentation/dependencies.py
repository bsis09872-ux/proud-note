from fastapi.security import HTTPBearer

from auth.application.service import AuthService

# Swagger 의 Authorize 버튼 + Authorization: Bearer <token> 파싱
bearer_scheme = HTTPBearer(auto_error=False, description="로그인으로 받은 access_token")


def provide_auth_service() -> AuthService:
    raise NotImplementedError("AuthService 의존성이 주입되지 않았습니다.")
