import importlib.metadata
from typing import ClassVar, override

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, TomlConfigSettingsSource

from backcat import configs


class ServerConfig(BaseSettings):
    log: configs.Log
    cors: configs.CORS
    csrf: configs.CSRF
    jwt: configs.JWT
    redis: configs.Redis

    # config loading options
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix="backcat_",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        toml_file="config.toml",
    )

    @property
    def version(self) -> str:
        return importlib.metadata.version("backcat")

    @classmethod
    @override
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,  # passed from code
            env_settings,  # loaded from active env variable
            dotenv_settings,  # loaded from .env file
            TomlConfigSettingsSource(settings_cls),  # loaded from toml config
            file_secret_settings,  # other file sources
        )
