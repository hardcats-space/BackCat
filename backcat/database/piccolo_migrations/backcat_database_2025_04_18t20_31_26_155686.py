from piccolo.apps.migrations.auto.migration_manager import MigrationManager

ID = "2025-04-18T20:31:26:155686"
VERSION = "1.24.1"
DESCRIPTION = "rename avatar to thumbnail"


async def forwards():
    manager = MigrationManager(migration_id=ID, app_name="", description=DESCRIPTION)

    def run():
        manager.rename_column(
            table_class_name="User",
            tablename="users",
            old_column_name="avatar",
            new_column_name="thumbnail",
            old_db_column_name="avatar",
            new_db_column_name="thumbnail",
            schema=None,
        )

    manager.add_raw(run)

    def run_backwards():
        manager.rename_column(
            table_class_name="User",
            tablename="users",
            old_column_name="thumbnail",
            new_column_name="avatar",
            old_db_column_name="thumbnail",
            new_db_column_name="avatar",
            schema=None,
        )

    manager.add_raw_backwards(run_backwards)

    return manager
