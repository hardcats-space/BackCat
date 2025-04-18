from contextlib import asynccontextmanager

import piccolo.apps.migrations.commands.forwards
from dishka import Provider, Scope, make_async_container
from dishka.integrations.litestar import (
    LitestarProvider,
    setup_dishka,
)
from litestar import Litestar, Router
from litestar.config.cors import CORSConfig
from litestar.config.csrf import CSRFConfig
from litestar.contrib.opentelemetry import OpenTelemetryConfig, OpenTelemetryPlugin
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import RedocRenderPlugin, SwaggerRenderPlugin
from litestar.plugins.prometheus import PrometheusConfig, PrometheusController
from litestar.plugins.structlog import StructlogConfig, StructlogPlugin
from piccolo.engine import engine_finder

from backcat.cmd.server import api
from backcat.cmd.server.config import ServerConfig

config = ServerConfig()  # type: ignore

provider = Provider(scope=Scope.APP)
provider.provide(lambda: config, provides=ServerConfig)


@asynccontextmanager
async def lifespan(app: Litestar):
    engine = engine_finder()
    assert engine is not None, "failed to load database engine"
    await engine.start_connection_pool()

    await piccolo.apps.migrations.commands.forwards.forwards("all")

    yield

    await engine.close_connection_pool()
    await app.state.dishka_container.close()


app = Litestar(
    debug=config.log.level == "DEBUG",
    route_handlers=[
        Router(
            "/api/v1",
            route_handlers=[
                api.v1.area.Controller,
                api.v1.booking.Controller,
                api.v1.camping.Controller,
                api.v1.health.Controller,
                api.v1.poi.Controller,
                api.v1.user.Controller,
            ],
        ),
        Router(
            "/api/extra",
            include_in_schema=False,
            route_handlers=[
                PrometheusController,
            ],
        ),
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
    openapi_config=OpenAPIConfig(
        title="backcat",
        version=config.version,
        path="/docs",
        render_plugins=[SwaggerRenderPlugin(), RedocRenderPlugin()],
    ),
    lifespan=[lifespan],
)

setup_dishka(container=make_async_container(provider, LitestarProvider()), app=app)
