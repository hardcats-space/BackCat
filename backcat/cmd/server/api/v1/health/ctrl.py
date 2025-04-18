import litestar
from dishka.integrations.litestar import FromDishka, inject

from backcat.cmd.server.api.v1.health import dto
from backcat.cmd.server.config import ServerConfig


class Controller(litestar.Controller):
    path = "/health"

    @litestar.get("")
    @inject
    async def health(self, config: FromDishka[ServerConfig]) -> dto.HealthDTO:
        return dto.HealthDTO(status="OK", version=config.version)
