from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns import BigInt, Varchar

ID = "2025-04-18T19:45:36:309546"
VERSION = "1.24.1"
DESCRIPTION = "add price to the area"


async def forwards():
    manager = MigrationManager(migration_id=ID, app_name="", description=DESCRIPTION)

    def run():
        manager.add_column(
            table_class_name="Area",
            tablename="areas",
            column_name="price_amount",
            db_column_name="price_amount",
            column_class_name="BigInt",
            column_class=BigInt,
            params={"null": False},
            schema=None,
        )

        manager.add_column(
            table_class_name="Area",
            tablename="areas",
            column_name="price_currency",
            db_column_name="price_currency",
            column_class_name="Varchar",
            column_class=Varchar,
            params={"length": 3, "null": False},
            schema=None,
        )

    manager.add_raw(run)

    def run_backwards():
        manager.drop_column(
            table_class_name="Area",
            tablename="areas",
            column_name="price_currency",
            db_column_name="price_currency",
            schema=None,
        )

        manager.drop_column(
            table_class_name="Area",
            tablename="areas",
            column_name="price_amount",
            db_column_name="price_amount",
            schema=None,
        )

    manager.add_raw_backwards(run_backwards)

    return manager
