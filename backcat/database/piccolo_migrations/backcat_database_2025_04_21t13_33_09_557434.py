from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.table import Table

from backcat.database import tables

ID = "2025-04-21T13:33:09:557434"
VERSION = "1.24.1"
DESCRIPTION = "add reviews table"


class SQL(Table): ...


async def forwards():
    manager = MigrationManager(migration_id=ID, app_name="", description=DESCRIPTION)

    async def run():
        await tables.Review.create_table()

    manager.add_raw(run)

    async def run_backwards():
        SQL.raw(f"DROP TABLE IF EXISTS {tables.Review._meta.tablename};")

    manager.add_raw_backwards(run_backwards)

    return manager
