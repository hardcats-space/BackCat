from datetime import UTC, datetime
from typing import Any, TypeVar, TypedDict, overload
from uuid import UUID

from piccolo.table import Table
from pydantic import BaseModel

from backcat import domain
from backcat.database import tables
from backcat.domain.base import DomainBaseModel


class ProjectionError(Exception): ...


DomainT = TypeVar("DomainT", bound=DomainBaseModel)


@overload
def projection(obj: dict[str, Any], *, cast_to: type[DomainT]) -> DomainT: ...


@overload
def projection(obj: tables.Area) -> domain.Area: ...


@overload
def projection(obj: tables.Booking) -> domain.Booking: ...


@overload
def projection(obj: tables.Camping) -> domain.Camping: ...


@overload
def projection(obj: tables.POI) -> domain.POI: ...


@overload
def projection(obj: tables.User) -> domain.User: ...


@overload
def projection(obj: domain.Area, *, camping_id: domain.CampingID) -> tables.Area: ...


@overload
def projection(obj: domain.Booking, *, user_id: domain.UserID, area_id: domain.AreaID) -> tables.Booking: ...


@overload
def projection(obj: domain.Camping, *, user_id: domain.UserID) -> tables.Camping: ...


@overload
def projection(obj: domain.POI, *, camping_id: domain.CampingID) -> tables.POI: ...


@overload
def projection(obj: domain.User) -> tables.User: ...


def projection(  # noqa: C901
    obj: BaseModel | Table | dict[str, Any],
    *,
    cast_to: type[DomainBaseModel] | None = None,
    area_id: domain.AreaID | None = None,
    camping_id: domain.CampingID | None = None,
    user_id: domain.UserID | None = None,
) -> BaseModel | Table | dict[str, Any]:
    match obj:
        case tables.Area():
            return _project_table_area_to_domain_area(obj)
        case tables.Booking():
            return _project_table_booking_to_domain_booking(obj)
        case tables.Camping():
            return _project_table_camping_to_domain_camping(obj)
        case tables.POI():
            return _project_table_poi_to_domain_poi(obj)
        case tables.User():
            return _project_table_user_to_domain_user(obj)
        case domain.Area():
            if camping_id is None:
                raise ProjectionError("camping_id is required for projection from domain.Area")
            return _project_domain_area_to_table_area(obj, camping_id)
        case domain.Booking():
            if area_id is None or user_id is None:
                raise ProjectionError("area_id and user_id are required for projection from domain.Booking")
            return _project_domain_booking_to_table_booking(obj, area_id, user_id)
        case domain.Camping():
            if user_id is None:
                raise ProjectionError("user_id is required for projection from domain.Camping")
            return _project_domain_camping_to_table_camping(obj, user_id)
        case domain.POI():
            if camping_id is None:
                raise ProjectionError("camping_id is required for projection from domain.POI")
            return _project_domain_poi_to_table_poi(obj, camping_id)
        case domain.User():
            return _project_domain_user_to_table_user(obj)

        case dict():
            if cast_to is None:
                raise ProjectionError("cast_to is required for projection from dict")

            obj.update(_project_table_common_dict(obj))
            return cast_to.model_validate(obj)
        case _:
            raise ProjectionError(f"unknown projection type: {type(obj)}")


class TableCommonProjection(TypedDict):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime


def _project_table_common(obj: tables.TableBaseModel) -> TableCommonProjection:
    return {
        "id": obj.id,  # type: ignore
        "created_at": obj.created_at.astimezone(UTC),  # type: ignore
        "updated_at": obj.updated_at.astimezone(UTC),  # type: ignore
        "deleted_at": obj.deleted_at.astimezone(UTC),  # type: ignore
    }


def _project_table_common_dict(obj: dict[str, Any]) -> TableCommonProjection:
    return {
        "id": obj["id"],  # type: ignore
        "created_at": obj["created_at"].astimezone(UTC),  # type: ignore
        "updated_at": obj["updated_at"].astimezone(UTC),  # type: ignore
        "deleted_at": obj["deleted_at"].astimezone(UTC),  # type: ignore
    }


def _project_table_area_to_domain_area(obj: tables.Area) -> domain.Area:
    return domain.Area(
        **_project_table_common(obj),
        polygon=[domain.Point(lat=point[0], lon=point[1]) for point in obj.polygon],
        description=obj.description,
        price=domain.Price(amount=obj.price_amount, currency=obj.price_currency),  # type: ignore
    )


def _project_table_booking_to_domain_booking(obj: tables.Booking) -> domain.Booking:
    return domain.Booking(
        **_project_table_common(obj),
        booked_since=obj.booked_since.astimezone(UTC),
        booked_till=obj.booked_till.astimezone(UTC),
    )


def _project_table_camping_to_domain_camping(obj: tables.Camping) -> domain.Camping:
    return domain.Camping(
        **_project_table_common(obj),
        polygon=[domain.Point(lat=point[0], lon=point[1]) for point in obj.polygon],
        description=obj.description,
        thumbnails=obj.thumbnails,
        title=obj.title,
    )


def _project_table_poi_to_domain_poi(obj: tables.POI) -> domain.POI:
    return domain.POI(
        **_project_table_common(obj),
        kind=domain.POIKind(obj.kind),
        point=domain.Point(lat=obj.lat, lon=obj.lon),
        name=obj.name,
        description=obj.description,
    )


def _project_table_user_to_domain_user(obj: tables.User) -> domain.User:
    return domain.User(
        **_project_table_common(obj),
        name=obj.name,
        thumbnail=obj.thumbnail,
    )


class DomainCommonProjection(TypedDict):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime


def _project_domain_common(obj: DomainBaseModel) -> DomainCommonProjection:
    return {
        "id": UUID(bytes=obj.id.bytes),
        "created_at": obj.created_at.astimezone(UTC),
        "updated_at": obj.updated_at.astimezone(UTC),
        "deleted_at": obj.deleted_at.astimezone(UTC),
    }


def _project_domain_area_to_table_area(obj: domain.Area, camping_id: domain.CampingID) -> tables.Area:
    return tables.Area(
        **_project_domain_common(obj),
        polygon=[[point.lat, point.lon] for point in obj.polygon],
        description=obj.description,
        price_amount=obj.price.amount,
        price_currency=str(obj.price.currency),
        camping=camping_id,
    )


def _project_domain_booking_to_table_booking(
    obj: domain.Booking, area_id: domain.AreaID, user_id: domain.UserID
) -> tables.Booking:
    return tables.Booking(
        **_project_domain_common(obj),
        booked_since=obj.booked_since.astimezone(UTC),
        booked_till=obj.booked_till.astimezone(UTC),
        area=area_id,
        user=user_id,
    )


def _project_domain_camping_to_table_camping(obj: domain.Camping, user_id: domain.UserID) -> tables.Camping:
    return tables.Camping(
        **_project_domain_common(obj),
        polygon=[[point.lat, point.lon] for point in obj.polygon],
        title=obj.title,
        description=obj.description,
        thumbnails=obj.thumbnails,
        user=user_id,
    )


def _project_domain_poi_to_table_poi(obj: domain.POI, camping_id: domain.CampingID) -> tables.POI:
    return tables.POI(
        **_project_domain_common(obj),
        kind=obj.kind.value,
        lat=obj.point.lat,
        lon=obj.point.lon,
        name=obj.name,
        description=obj.description,
        camping=camping_id,
    )


def _project_domain_user_to_table_user(obj: domain.User) -> tables.User:
    return tables.User(
        **_project_domain_common(obj),
        name=obj.name,
        thumbnail=obj.thumbnail,
    )
