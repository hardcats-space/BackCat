from __future__ import annotations

from pathlib import Path
from typing import Protocol, override

from aiobotocore.session import get_session  # pyright: ignore[reportMissingTypeStubs,reportUnknownVariableType]

from backcat import configs
from backcat.services import errors


class FileStorage(Protocol):
    async def get_url(self, path: Path) -> str: ...

    async def upload(self, path: Path, data: bytes): ...

    async def download(self, path: Path) -> bytes: ...


class FileStorageImpl(FileStorage):
    def __init__(self, cfg: configs.S3):
        self._cfg = cfg

    @override
    async def get_url(self, path: Path) -> str:
        if self._cfg.public_endpoint is None:
            return f"https://{self._cfg.bucket}.{self._cfg.endpoint}/{path.as_posix()}"

        return f"https://{self._cfg.public_endpoint}/{path.as_posix()}"

    @override
    async def upload(self, path: Path, data: bytes):
        try:
            async with get_session().create_client(
                "s3",
                region_name=self._cfg.region,
                endpoint_url=f"https://{self._cfg.endpoint}",
                aws_access_key_id=self._cfg.access_key,
                aws_secret_access_key=self._cfg.secret_key,
            ) as client:
                await client.put_object(Bucket=self._cfg.bucket, Key=path.as_posix(), Body=data)  # type: ignore
        except Exception as e:
            raise errors.InternalServerError("failed to save file") from e

    @override
    async def download(self, path: Path) -> bytes:
        try:
            async with get_session().create_client(
                "s3",
                region_name=self._cfg.region,
                endpoint_url=f"https://{self._cfg.endpoint}",
                aws_access_key_id=self._cfg.access_key,
                aws_secret_access_key=self._cfg.secret_key,
            ) as client:
                response = await client.get_object(Bucket=self._bucket_name, Key=path.as_posix())  # type: ignore
                return response["Body"].read()
        except Exception as e:
            raise errors.InternalServerError("failed to load file") from e
