from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.base import OnDelete, OnUpdate
from piccolo.columns.column_types import UUID, ForeignKey, Timestamp, Timestamptz
from piccolo.columns.defaults.timestamp import TimestampNow
from piccolo.columns.defaults.timestamptz import TimestamptzNow
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


ID = "2025-04-23T11:03:30:697988"
VERSION = "1.24.1"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(migration_id=ID, app_name="backcat_database", description=DESCRIPTION)

    manager.add_column(
        table_class_name="Area",
        tablename="areas",
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

    manager.alter_column(
        table_class_name="Area",
        tablename="areas",
        column_name="created_at",
        db_column_name="created_at",
        params={"default": TimestamptzNow()},
        old_params={"default": TimestampNow()},
        column_class=Timestamptz,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Area",
        tablename="areas",
        column_name="updated_at",
        db_column_name="updated_at",
        params={"default": TimestamptzNow()},
        old_params={"default": TimestampNow()},
        column_class=Timestamptz,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Area",
        tablename="areas",
        column_name="deleted_at",
        db_column_name="deleted_at",
        params={},
        old_params={},
        column_class=Timestamptz,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Booking",
        tablename="bookings",
        column_name="created_at",
        db_column_name="created_at",
        params={"default": TimestamptzNow()},
        old_params={"default": TimestampNow()},
        column_class=Timestamptz,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Booking",
        tablename="bookings",
        column_name="updated_at",
        db_column_name="updated_at",
        params={"default": TimestamptzNow()},
        old_params={"default": TimestampNow()},
        column_class=Timestamptz,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Booking",
        tablename="bookings",
        column_name="deleted_at",
        db_column_name="deleted_at",
        params={},
        old_params={},
        column_class=Timestamptz,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Booking",
        tablename="bookings",
        column_name="booked_since",
        db_column_name="booked_since",
        params={"default": TimestamptzNow()},
        old_params={"default": TimestampNow()},
        column_class=Timestamptz,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Booking",
        tablename="bookings",
        column_name="booked_till",
        db_column_name="booked_till",
        params={"default": TimestamptzNow()},
        old_params={"default": TimestampNow()},
        column_class=Timestamptz,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Camping",
        tablename="campings",
        column_name="created_at",
        db_column_name="created_at",
        params={"default": TimestamptzNow()},
        old_params={"default": TimestampNow()},
        column_class=Timestamptz,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Camping",
        tablename="campings",
        column_name="updated_at",
        db_column_name="updated_at",
        params={"default": TimestamptzNow()},
        old_params={"default": TimestampNow()},
        column_class=Timestamptz,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Camping",
        tablename="campings",
        column_name="deleted_at",
        db_column_name="deleted_at",
        params={},
        old_params={},
        column_class=Timestamptz,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="POI",
        tablename="pois",
        column_name="created_at",
        db_column_name="created_at",
        params={"default": TimestamptzNow()},
        old_params={"default": TimestampNow()},
        column_class=Timestamptz,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="POI",
        tablename="pois",
        column_name="updated_at",
        db_column_name="updated_at",
        params={"default": TimestamptzNow()},
        old_params={"default": TimestampNow()},
        column_class=Timestamptz,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="POI",
        tablename="pois",
        column_name="deleted_at",
        db_column_name="deleted_at",
        params={},
        old_params={},
        column_class=Timestamptz,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Review",
        tablename="reviews",
        column_name="created_at",
        db_column_name="created_at",
        params={"default": TimestamptzNow()},
        old_params={"default": TimestampNow()},
        column_class=Timestamptz,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Review",
        tablename="reviews",
        column_name="updated_at",
        db_column_name="updated_at",
        params={"default": TimestamptzNow()},
        old_params={"default": TimestampNow()},
        column_class=Timestamptz,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="Review",
        tablename="reviews",
        column_name="deleted_at",
        db_column_name="deleted_at",
        params={},
        old_params={},
        column_class=Timestamptz,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="User",
        tablename="users",
        column_name="created_at",
        db_column_name="created_at",
        params={"default": TimestamptzNow()},
        old_params={"default": TimestampNow()},
        column_class=Timestamptz,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="User",
        tablename="users",
        column_name="updated_at",
        db_column_name="updated_at",
        params={"default": TimestamptzNow()},
        old_params={"default": TimestampNow()},
        column_class=Timestamptz,
        old_column_class=Timestamp,
        schema=None,
    )

    manager.alter_column(
        table_class_name="User",
        tablename="users",
        column_name="deleted_at",
        db_column_name="deleted_at",
        params={},
        old_params={},
        column_class=Timestamptz,
        old_column_class=Timestamp,
        schema=None,
    )

    return manager
