from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

from dishka import AsyncContainer
from litestar.connection import ASGIConnection
from litestar.security.jwt import Token

from backcat import domain, services

RetrieveF = Callable[[Token, ASGIConnection[Any, Any, Any, Any]], Awaitable[domain.User | None]]
RevokedF = Callable[[Token, ASGIConnection[Any, Any, Any, Any]], Awaitable[bool]]


def retrieve_user_factory(container: AsyncContainer) -> RetrieveF:
    # Unfortunately, we can not use `inject` here, because this function is called as simple callback
    # from oauth2 middleware, so we can not inject the container. Therefore, we have to manually
    # provide IoC using factory pattern.
    async def retrieve_user(token: Token, connection: ASGIConnection[Any, Any, Any, Any]) -> domain.User | None:
        user_repo = await container.get(services.UserRepo)

        try:
            user_id = UUID(token.sub, version=4)
        except ValueError:
            return None

        return await user_repo.read_user(user_id)

    return retrieve_user


def revoked_token_factory(container: AsyncContainer) -> RevokedF:
    async def revoked_token(token: Token, connection: ASGIConnection[Any, Any, Any, Any]) -> bool:
        token_repo = await container.get(services.TokenRepo)

        if token.jti is None:
            return False

        try:
            return await token_repo.is_banned(token.jti)
        except Exception:
            return False

    return revoked_token
