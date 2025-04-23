from contextlib import asynccontextmanager
from datetime import timedelta

import piccolo.apps.migrations.commands.forwards
from dishka import Provider, Scope, make_async_container
from dishka.integrations.litestar import LitestarProvider, setup_dishka
from litestar import Litestar, Router
from litestar.config.cors import CORSConfig
from litestar.config.csrf import CSRFConfig
from litestar.contrib.opentelemetry import OpenTelemetryConfig, OpenTelemetryPlugin
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin, SwaggerRenderPlugin
from litestar.plugins.prometheus import PrometheusConfig, PrometheusController
from litestar.plugins.structlog import StructlogConfig, StructlogPlugin
from litestar.security.jwt import OAuth2PasswordBearerAuth
from piccolo.engine import engine_finder

from backcat import configs, domain, services
from backcat.cmd.server import api, authorization
from backcat.cmd.server.config import ServerConfig

config = ServerConfig()  # type: ignore

provider = Provider(scope=Scope.APP)
provider.provide(lambda: config, provides=ServerConfig)
provider.provide(lambda: config.cors, provides=configs.CORS)
provider.provide(lambda: config.csrf, provides=configs.CSRF)
provider.provide(lambda: config.jwt, provides=configs.JWT)
provider.provide(lambda: config.redis, provides=configs.Redis)
provider.provide(lambda: config.s3, provides=configs.S3)
provider.provide(services.Cache, provides=services.Cache)
provider.provide(services.AreaRepoImpl, provides=services.AreaRepo)
provider.provide(services.BookingRepoImpl, provides=services.BookingRepo)
provider.provide(services.CampingRepoImpl, provides=services.CampingRepo)
provider.provide(services.POIRepoImpl, provides=services.POIRepo)
provider.provide(services.UserRepoImpl, provides=services.UserRepo)
provider.provide(services.TokenRepoImpl, provides=services.TokenRepo)
provider.provide(services.FileStorageImpl, provides=services.FileStorage)
provider.provide(lambda: oauth2, provides=OAuth2PasswordBearerAuth[domain.User])  # note: global scope capture
container = make_async_container(provider, LitestarProvider())

oauth2 = OAuth2PasswordBearerAuth[domain.User](
    retrieve_user_handler=authorization.retrieve_user_factory(container),
    revoked_token_handler=authorization.revoked_token_factory(container),
    token_secret=config.jwt.secret,
    token_url="/api/v1/user/oauth2/token",
    exclude=[
        "/api/v1/user/oauth2/token",
        "/api/v1/user/sign-in",
        "/api/v1/user/sign-up",
        "/api/schema/*",
        "/api/extra/*",
    ],
    algorithm=config.jwt.algorithm,
    accepted_audiences=["backcat"],
    accepted_issuers=["backcat"],
    strict_audience=True,
    default_token_expiration=timedelta(seconds=config.jwt.token_expires),
)


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
        path="/api/schema",
        render_plugins=[
            SwaggerRenderPlugin(path="/swagger"),
            ScalarRenderPlugin(path="/scalar"),
        ],
    ),
    lifespan=[lifespan],
    on_app_init=[oauth2.on_app_init],
)


setup_dishka(container=container, app=app)
