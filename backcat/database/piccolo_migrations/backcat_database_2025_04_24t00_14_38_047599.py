from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.base import OnDelete
from piccolo.columns.base import OnUpdate
from piccolo.columns.column_types import ForeignKey
from piccolo.columns.column_types import UUID
from piccolo.columns.defaults.uuid import UUID4
from piccolo.columns.indexes import IndexMethod
from piccolo.table import Table


class User(Table, tablename="users", schema=None):
    id = UUID(
        default=UUID4(),
        null=False,
        primary_key=True,
        unique=False,
        index=False,
        index_method=IndexMethod.hash,
        choices=None,
        db_column_name=None,
        secret=False,
    )
    id = UUID(
        default=UUID4(),
        null=False,
        primary_key=True,
        unique=False,
        index=False,
        index_method=IndexMethod.hash,
        choices=None,
        db_column_name=None,
        secret=False,
    )


ID = "2025-04-24T00:14:38:047599"
VERSION = "1.24.1"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="backcat_database", description=DESCRIPTION
    )

    manager.add_column(
        table_class_name="POI",
        tablename="pois",
        column_name="user",
        db_column_name="user",
        column_class_name="ForeignKey",
        column_class=ForeignKey,
        params={
            "references": User,
            "on_delete": OnDelete.cascade,
            "on_update": OnUpdate.cascade,
            "target_column": "id",
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": IndexMethod.btree,
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema=None,
    )

    return manager
