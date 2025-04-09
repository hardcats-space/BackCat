from contextlib import asynccontextmanager

from dishka import Provider, Scope, make_async_container
from dishka.integrations.litestar import (
    LitestarProvider,
    setup_dishka,
)
from litestar import Litestar, Router
from litestar.config.cors import CORSConfig
from litestar.config.csrf import CSRFConfig
from litestar.contrib.opentelemetry import OpenTelemetryConfig, OpenTelemetryPlugin
from litestar.plugins.prometheus import PrometheusConfig, PrometheusController
from litestar.plugins.structlog import StructlogConfig, StructlogPlugin

from backcat.cmd.server import api
from backcat.cmd.server.config import ServerConfig

config = ServerConfig()  # type: ignore

provider = Provider(scope=Scope.APP)
provider.provide(lambda: config, provides=ServerConfig)


@asynccontextmanager
async def lifespan(app: Litestar):
    yield
    await app.state.dishka_container.close()


app = Litestar(
    debug=config.log.level == "DEBUG",
    route_handlers=[
        Router("/api/v1/health", route_handlers=[api.v1.health.Controller]),
        PrometheusController,
    ],
    plugins=[
        StructlogPlugin(StructlogConfig()),
        OpenTelemetryPlugin(OpenTelemetryConfig()),
    ],
    middleware=[
        PrometheusConfig(
            app_name="backcat",
            prefix="backcat",
            labels={"app": "backcat", "version": config.version},
            excluded_http_methods=["OPTIONS"],
        ).middleware
    ],
    cors_config=CORSConfig(
        allow_origins=config.cors.allow_origins,
        allow_methods=config.cors.allow_methods,  # type: ignore
        allow_headers=config.cors.allow_headers,
        allow_credentials=config.cors.allow_credentials,
        expose_headers=config.cors.expose_headers,
        max_age=config.cors.max_age,
    ),
    csrf_config=CSRFConfig(
        secret=config.csrf.secret,
        cookie_name=config.csrf.cookie_name,
        cookie_path=config.csrf.cookie_path,
        cookie_secure=config.csrf.cookie_secure,
        cookie_httponly=config.csrf.cookie_httponly,
        cookie_samesite=config.csrf.cookie_samesite,
        cookie_domain=config.csrf.cookie_domain,
    )
    if config.csrf.enabled
    else None,
    lifespan=[lifespan],
)

setup_dishka(container=make_async_container(provider, LitestarProvider()), app=app)
