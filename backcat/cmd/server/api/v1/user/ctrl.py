import litestar

from backcat import domain
from backcat.cmd.server.api.v1.user import dto


class Controller(litestar.Controller):
    path = "/user"

    @litestar.post("/sign-up", dto=dto.SignUpUserRequest, return_dto=dto.SignUpUserResponse)
    async def signup(self, data: domain.User) -> domain.User:
        raise NotImplementedError

    @litestar.post("/sign-in", dto=dto.SignInUserRequest, return_dto=dto.SignInUserResponse)
    async def signin(self, data: domain.User) -> domain.User:
        raise NotImplementedError

    @litestar.post("/sign-out")
    async def signout(self) -> domain.User:
        raise NotImplementedError

    @litestar.get("/me", return_dto=dto.UserProfileResponse)
    async def profile(self) -> domain.User:
        raise NotImplementedError
