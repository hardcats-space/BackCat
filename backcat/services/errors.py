class ServiceError(Exception):
    status_code: int


class ValidationError(ServiceError):
    """input data is malformed"""

    status_code: int = 422


class NotFoundError(ServiceError):
    """resource not found"""

    status_code: int = 404


class ConflictError(ServiceError):
    """resource already exists or anther constraint violation"""

    status_code: int = 409


class AcccessDeniedError(ServiceError):
    """access denied"""

    status_code: int = 403


class ConversionError(ServiceError):
    """failed to convert db data to domain model"""

    status_code: int = 500


class InternalServerError(ServiceError):
    """internal server error"""

    status_code: int = 500
