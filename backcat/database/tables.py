from datetime import datetime
from typing import Protocol

from piccolo.columns import UUID, Array, BigInt, DoublePrecision, ForeignKey, SmallInt, Timestamp, Varchar
from piccolo.columns.defaults import TimestampNow
from piccolo.columns.indexes import IndexMethod
from piccolo.table import Table

from backcat import domain


class TableBaseModel(Protocol):
    id = UUID()
    created_at = Timestamp()
    updated_at = Timestamp()
    deleted_at = Timestamp()


class User(Table, tablename="users"):
    id = UUID(primary_key=True, index_method=IndexMethod.hash)

    created_at = Timestamp(default=TimestampNow(), null=False)
    updated_at = Timestamp(auto_update=datetime.now, null=False)
    deleted_at = Timestamp(default=None, null=True)

    name = Varchar(length=150, null=False)
    email = Varchar(length=255, null=False)
    password = Varchar(length=512, null=False)
    thumbnail = Varchar(null=True)


class Camping(Table, tablename="campings"):
    """Closed polygon representing some camping org."""

    id = UUID(primary_key=True, index_method=IndexMethod.hash)

    created_at = Timestamp(default=TimestampNow(), null=False)
    updated_at = Timestamp(auto_update=datetime.now, null=False)
    deleted_at = Timestamp(default=None, null=True)

    polygon = Array(base_column=Array(base_column=DoublePrecision()), null=False)
    title = Varchar(length=250, null=False)
    description = Varchar(length=5000, null=True)
    thumbnails = Array(base_column=Varchar(255), null=False)

    user = ForeignKey(references=User, null=False, target_column=User.id)


class Area(Table, tablename="areas"):
    """Area represents some polygon on map available for booking"""

    id = UUID(primary_key=True, index_method=IndexMethod.hash)

    created_at = Timestamp(default=TimestampNow(), null=False)
    updated_at = Timestamp(auto_update=datetime.now, null=False)
    deleted_at = Timestamp(default=None, null=True)

    polygon = Array(base_column=Array(base_column=DoublePrecision()), null=False)
    description = Varchar(length=5000, null=True)
    price_amount = BigInt(null=False)
    price_currency = Varchar(length=3, null=False)

    camping = ForeignKey(references=Camping, null=False, target_column=Camping.id)
    """camping in which this area is available for booking"""


class POI(Table, tablename="pois"):
    id = UUID(primary_key=True, index_method=IndexMethod.hash)

    created_at = Timestamp(default=TimestampNow(), null=False)
    updated_at = Timestamp(auto_update=datetime.now, null=False)
    deleted_at = Timestamp(default=None, null=True)

    kind = Varchar(choices=domain.POIKind, default=domain.POIKind.GENERAL, null=False)
    lat: DoublePrecision
    lon: DoublePrecision
    name = Varchar(length=150, null=True)
    description = Varchar(length=5000, null=True)

    camping = ForeignKey(references=Camping, null=False, target_column=Camping.id)
    """camping in which this poi is located"""


class Booking(Table, tablename="bookings"):
    id = UUID(primary_key=True, index_method=IndexMethod.hash)

    created_at = Timestamp(default=TimestampNow(), null=False)
    updated_at = Timestamp(auto_update=datetime.now, null=False)
    deleted_at = Timestamp(default=None, null=True)

    booked_since = Timestamp(null=False)
    booked_till = Timestamp(null=False)

    area = ForeignKey(references=Area, null=False, target_column=Area.id)
    user = ForeignKey(references=User, null=False, target_column=User.id)


class Review(Table, tablename="reviews"):
    id = UUID(primary_key=True, index_method=IndexMethod.hash)

    created_at = Timestamp(default=TimestampNow(), null=False)
    updated_at = Timestamp(auto_update=datetime.now, null=False)
    deleted_at = Timestamp(default=None, null=True)

    rating = SmallInt(null=False)
    comment = Varchar(length=5000, null=True)

    area = ForeignKey(references=Area, null=False, target_column=Area.id)
    user = ForeignKey(references=User, null=False, target_column=User.id)
