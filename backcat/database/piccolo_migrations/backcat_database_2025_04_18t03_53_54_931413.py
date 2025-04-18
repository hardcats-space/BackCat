from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.table import Table

from backcat.database import tables

ID = "2025-04-18T03:53:54:931413"
VERSION = "1.24.1"
DESCRIPTION = "initial creation of tables"


class SQL(Table): ...


async def forwards():
    manager = MigrationManager(migration_id=ID, app_name="", description=DESCRIPTION)

    async def run():
        await tables.User.create_table()
        await tables.Camping.create_table()
        await tables.Area.create_table()
        await tables.POI.create_table()
        await tables.Booking.create_table()

    manager.add_raw(run)

    async def run_backwards():
        SQL.raw(f"DROP TABLE IF EXISTS {tables.Booking._meta.tablename};")
        SQL.raw(f"DROP TABLE IF EXISTS {tables.POI._meta.tablename};")
        SQL.raw(f"DROP TABLE IF EXISTS {tables.Area._meta.tablename};")
        SQL.raw(f"DROP TABLE IF EXISTS {tables.Camping._meta.tablename};")
        SQL.raw(f"DROP TABLE IF EXISTS {tables.User._meta.tablename};")

    manager.add_raw_backwards(run_backwards)

    return manager
