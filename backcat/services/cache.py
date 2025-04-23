from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, TypeVar, overload

import pydantic
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


T = TypeVar("T", bound=pydantic.BaseModel)


class Cache:
    LIVE_FEAT = timedelta(seconds=10)
    HOT_FEAT = timedelta(minutes=5)
    COLD_FEAT = timedelta(minutes=30)

    def __init__(self, redis_dns: pydantic.RedisDsn):
        self._redis = Redis.from_url(redis_dns.unicode_string())

    @overload
    async def get(self, key: Key, *, silent: bool = True) -> dict[str, Any] | None: ...

    @overload
    async def get(self, key: Key, *, t: type[T], silent: bool = True) -> T | None: ...

    async def get(self, key: Key, *, t: type[T] | None = None, silent: bool = True) -> T | dict[str, Any] | None:
        try:
            value = await self._redis.get(key.as_str())
            if value is None:
                return None

            if t is None:
                return json.loads(value)

            return t.model_validate_json(value)
        except Exception as e:
            if not silent:
                raise e

    async def set(
        self,
        key: Key,
        value: pydantic.BaseModel | dict,
        *,
        expire: timedelta | None = None,
        silent: bool = True,
    ):
        try:
            if isinstance(value, dict):
                value_json = json.dumps(value)
            else:
                value_json = value.model_dump_json()

            await self._redis.set(key.as_str(), value_json, ex=expire)
        except Exception as e:
            if not silent:
                raise e

    async def invalidate(self, key: Key):
        await self._redis.delete(key.as_str())
