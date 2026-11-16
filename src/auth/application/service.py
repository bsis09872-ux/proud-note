from auth.application.dto import LoginCommand
from auth.domain.entities import IssuedToken, TokenPayload
from auth.domain.exceptions import InvalidCredentials, TokenRevoked
from auth.domain.repository import TokenBlacklistRepository
from auth.domain.service import TokenProvider, UserCredentialVerifier
from shared.core.models import utcnow


class AuthService:
    def __init__(
        self,
        credential_verifier: UserCredentialVerifier,
        blacklist_repo: TokenBlacklistRepository,
        token_provider: TokenProvider,
    ):
        self._verifier = credential_verifier
        self._blacklist = blacklist_repo
        self._tokens = token_provider

    async def login(self, command: LoginCommand) -> IssuedToken:
        user_id = await self._verifier.verify(command.email, command.password)
        if user_id is None:
            raise InvalidCredentials()
        return self._tokens.issue(user_id)

    async def logout(self, token: str) -> None:
        payload = self._tokens.decode(token)
        await self._blacklist.add(payload.jti, payload.exp)
        await self._blacklist.cleanup_expired(utcnow())

    async def authenticate(self, token: str) -> TokenPayload:
        payload = self._tokens.decode(token)
        if await self._blacklist.is_blacklisted(payload.jti):
            raise TokenRevoked()
        return payload
