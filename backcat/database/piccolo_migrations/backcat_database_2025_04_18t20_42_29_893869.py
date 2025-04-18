from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns import Array, Varchar

ID = "2025-04-18T20:42:29:893869"
VERSION = "1.24.1"
DESCRIPTION = "add thumbnails to camping"


async def forwards():
    manager = MigrationManager(migration_id=ID, app_name="", description=DESCRIPTION)

    def run():
        manager.add_column(
            table_class_name="Camping",
            tablename="campings",
            column_name="thumbnails",
            db_column_name="thumbnails",
            column_class_name="Array",
            column_class=Array,
            params={
                "base_column": Varchar(
                    length=255,
                    null=False,
                ),
                "default": list,
                "null": False,
            },
            schema=None,
        )

    manager.add_raw(run)

    async def run_backwards():
        manager.drop_column(
            table_class_name="Camping",
            tablename="campings",
            column_name="thumbnails",
            db_column_name="thumbnails",
            schema=None,
        )

    manager.add_raw_backwards(run_backwards)

    return manager
