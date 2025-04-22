import os

from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine

DB = PostgresEngine(
    config={
        "host": os.environ.get("POSTGRES_HOSTNAME", "localhost"),
        "port": os.environ.get("POSTGRES_PORT", 5432),
        "user": os.environ.get("POSTGRES_USERNAME", "postgres"),
        "password": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "database": os.environ.get("POSTGRES_DATABASE", "postgres"),
    }
)


APP_REGISTRY = AppRegistry(apps=["backcat.database.piccolo_app"])
