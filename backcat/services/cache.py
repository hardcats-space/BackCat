from __future__ import annotations

from dataclasses import dataclass
from typing import Any, overload

import msgspec
from redis.asyncio import Redis


@dataclass
class Keyspace:
    name: str

    def key(self, *path: str) -> Key:
        return Key(self, list(path))


@dataclass
class Key:
    ks: Keyspace
    path: list[str]

    def as_str(self):
        return f"{self.ks.name}:{':'.join(self.path)}"


class Cache:
    def __init__(self, redis_dns):
        self._redis = Redis.from_url(redis_dns)

    @overload
    async def get(self, key: Key) -> dict[str, Any] | None: ...

    @overload
    async def get(self, key: Key, t: type[msgspec.Struct]) -> msgspec.Struct | None: ...

    async def get(self, key: Key, t: type[msgspec.Struct] | None = None) -> msgspec.Struct | dict[str, Any] | None:
        value = await self._redis.get(key.as_str())
        if value is None:
            return None
        return msgspec.json.decode(value, type=t)

    async def set(self, key: Key, value: msgspec.Struct | dict):
        await self._redis.set(key.as_str(), msgspec.json.encode(value))

    async def invalidate(self, key: Key):
        await self._redis.delete(key.as_str())
