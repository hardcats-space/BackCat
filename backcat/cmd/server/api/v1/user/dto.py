from litestar.dto import DTOConfig
from litestar.plugins.pydantic import PydanticDTO

from backcat import domain


class SignUpUserRequest(PydanticDTO[domain.User]):
    config = DTOConfig(include={"email", "name", "password"})


class SignUpUserResponse(PydanticDTO[domain.User]):
    config = DTOConfig(exclude={"password"})


class SignInUserRequest(PydanticDTO[domain.User]):
    config = DTOConfig(include={"email", "password"})


class SignInUserResponse(PydanticDTO[domain.User]):
    config = DTOConfig(exclude={"password"})


class UserProfileResponse(PydanticDTO[domain.User]):
    config = DTOConfig(exclude={"password"})
