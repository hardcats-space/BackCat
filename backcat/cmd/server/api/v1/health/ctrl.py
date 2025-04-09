import litestar
from dishka.integrations.litestar import FromDishka, inject

from backcat.cmd.server.api.v1.health.dto import HealthDTO
from backcat.cmd.server.config import ServerConfig


class Controller(litestar.Controller):
    path = "/"

    @litestar.get("")
    @inject
    async def _(self, config: FromDishka[ServerConfig]) -> HealthDTO:
        return HealthDTO(status="OK", version=config.version)
