from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import DoublePrecision
from piccolo.columns.indexes import IndexMethod

ID = "2025-04-24T16:16:11:089270"
VERSION = "1.24.1"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(migration_id=ID, app_name="backcat_database", description=DESCRIPTION)

    manager.add_column(
        table_class_name="POI",
        tablename="pois",
        column_name="lat",
        db_column_name="lat",
        column_class_name="DoublePrecision",
        column_class=DoublePrecision,
        params={
            "default": 0.0,
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

    manager.add_column(
        table_class_name="POI",
        tablename="pois",
        column_name="lon",
        db_column_name="lon",
        column_class_name="DoublePrecision",
        column_class=DoublePrecision,
        params={
            "default": 0.0,
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
