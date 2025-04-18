from litestar.dto import DTOConfig
from litestar.plugins.pydantic import PydanticDTO

from backcat import domain


class SignUpUserRequest(PydanticDTO[domain.User]):
    config = DTOConfig(include={"email", "name", "password"}, rename_strategy="camel")


class SignUpUserResponse(PydanticDTO[domain.User]):
    config = DTOConfig(exclude={"password"}, rename_strategy="camel")


class SignInUserRequest(PydanticDTO[domain.User]):
    config = DTOConfig(include={"email", "password"}, rename_strategy="camel")


class SignInUserResponse(PydanticDTO[domain.User]):
    config = DTOConfig(exclude={"password"}, rename_strategy="camel")


class UserProfileResponse(PydanticDTO[domain.User]):
    config = DTOConfig(exclude={"password"}, rename_strategy="camel")


class UpdateUserRequest(PydanticDTO[domain.User]):
    config = DTOConfig(
        exclude={"password", "id", "created_at", "updated_at", "deleted_at"}, partial=True, rename_strategy="camel"
    )


class UpdateUserResponse(PydanticDTO[domain.User]):
    config = DTOConfig(exclude={"password"}, rename_strategy="camel")
