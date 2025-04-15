import os

from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine

DB = PostgresEngine(
    config={
        "host": os.environ.get("POSTGRES_HOSTNAME"),
        "port": os.environ.get("POSTGRES_PORT", 5432),
        "user": os.environ.get("POSTGRES_USERNAME"),
        "password": os.environ.get("POSTGRES_PASSWORD"),
        "database": os.environ.get("POSTGRES_DATABASE"),
    }
)


APP_REGISTRY = AppRegistry(apps=[])
