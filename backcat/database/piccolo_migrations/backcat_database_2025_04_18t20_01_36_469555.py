from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns import Varchar

ID = "2025-04-18T20:01:36:469555"
VERSION = "1.24.1"
DESCRIPTION = "add description to objects"


async def forwards():
    manager = MigrationManager(migration_id=ID, app_name="", description=DESCRIPTION)

    def run():
        manager.add_column(
            table_class_name="Camping",
            tablename="campings",
            column_name="description",
            db_column_name="description",
            column_class_name="Varchar",
            column_class=Varchar,
            params={"length": 5000, "null": True},
            schema=None,
        )

    manager.add_raw(run)

    def run_backwards():
        manager.drop_column(
            table_class_name="Camping",
            tablename="campings",
            column_name="description",
            db_column_name="description",
            schema=None,
        )

    manager.add_raw_backwards(run_backwards)

    return manager
