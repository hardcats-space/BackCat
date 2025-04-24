from litestar.exceptions import HTTPException
from litestar.types import ASGIApp, Receive, Scope, Send

from backcat.services import errors


def service_error_middleware(app: ASGIApp) -> ASGIApp:
    async def service_error_handler(scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await app(scope, receive, send)
        except errors.ServiceError as e:
            raise HTTPException(status_code=e.status_code, detail=str(e)) from e
        except Exception as e:
            raise e

    return service_error_handler
