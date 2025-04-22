from typing import Protocol

from backcat.services.cache import Cache, Keyspace


class TokenRepo(Protocol):
    async def ban(self, token_id: str) -> None: ...
    async def unban(self, token_id: str) -> None: ...
    async def is_banned(self, token_id: str) -> bool: ...


class TokenRepoImpl(TokenRepo):
    def __init__(self, cache: Cache):
        self._ks = Keyspace("token")
        self._cache = cache

    async def ban(self, token_id: str) -> None:
        await self._cache.set(self._ks.key(token_id), {"blacklisted": True}, expire=self._cache.HOT_FEAT)

    async def unban(self, token_id: str) -> None:
        await self._cache.invalidate(self._ks.key(token_id))

    async def is_banned(self, token_id: str) -> bool:
        data = await self._cache.get(self._ks.key(token_id))
        if data is None:
            return False
        return data.get("blacklisted", False)
