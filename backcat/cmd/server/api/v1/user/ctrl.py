from typing import Annotated, Any
from uuid import uuid4

import litestar
from dishka.integrations.litestar import FromDishka, inject
from litestar.dto import DTOData
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotAuthorizedException
from litestar.params import Body
from litestar.security.jwt import OAuth2Login, OAuth2PasswordBearerAuth, Token

from backcat import domain, services
from backcat.cmd.server.api.v1.user import dto


class Controller(litestar.Controller):
    path = "/user"
    tags = ["user"]

    @litestar.post("/oauth2/token", dto=dto.Oauth2TokenRequest, return_dto=None)
    @inject
    async def oauth2_token(
        self,
        data: Annotated[DTOData[domain.User], Body(media_type=RequestEncodingType.URL_ENCODED)],
        oauth2: FromDishka[OAuth2PasswordBearerAuth[domain.User]],
        user_repo: FromDishka[services.UserRepo],
    ) -> litestar.Response[OAuth2Login]:
        """OAuth2 compliant /login endpoint"""
        signin = data.as_builtins()
        user = await user_repo.retrieve_verify_user(signin["email"], signin["password"])
        return oauth2.login(
            identifier=user.id.hex,
            token_issuer="backcat",
            token_audience="backcat",
        )

    @litestar.post("/oauth2/refresh", dto=dto.Oauth2TokenRequest, return_dto=None)
    @inject
    async def oauth2_refresh(
        self,
        request: litestar.Request[domain.User, Any, Any],
        oauth2: FromDishka[OAuth2PasswordBearerAuth[domain.User]],
        user_repo: FromDishka[services.UserRepo],
    ) -> litestar.Response[Token]:
        """OAuth2 compliant /refresh endpoint"""
        user = await user_repo.read_user(request.user.id)
        if user is None:
            raise NotAuthorizedException(detail="user no longer exists")
        return oauth2.login(
            identifier=user.id.hex,
            token_issuer="backcat",
            token_audience="backcat",
        )

    @litestar.post("/sign-up", dto=dto.SignUpUserRequest, return_dto=dto.SignUpUserResponse)
    @inject
    async def signup(
        self,
        data: DTOData[domain.User],
        oauth2: FromDishka[OAuth2PasswordBearerAuth[domain.User]],
        user_repo: FromDishka[services.UserRepo],
    ) -> litestar.Response[domain.User]:
        """Custom /sign-up endpoint"""
        user = await user_repo.create_user(data.create_instance(**domain.User.new_defaults_kwargs()))
        return oauth2.login(
            identifier=user.id.hex,
            response_body=user,
            token_issuer="backcat",
            token_audience="backcat",
        )

    @litestar.post("/sign-in", dto=dto.SignInUserRequest, return_dto=dto.SignInUserResponse)
    @inject
    async def signin(
        self,
        data: DTOData[domain.User],
        oauth2: FromDishka[OAuth2PasswordBearerAuth[domain.User]],
        user_repo: FromDishka[services.UserRepo],
    ) -> litestar.Response[domain.User]:
        """Custom /sign-in endpoint"""
        signin = data.as_builtins()
        user = await user_repo.retrieve_verify_user(signin["email"], signin["password"])
        return oauth2.login(
            identifier=user.id.hex,
            response_body=user,
            token_issuer="backcat",
            token_audience="backcat",
        )

    @litestar.post("/refresh", return_dto=dto.SignInUserResponse)
    @inject
    async def refresh(
        self,
        request: litestar.Request[domain.User, Token, Any],
        oauth2: FromDishka[OAuth2PasswordBearerAuth[domain.User]],
        user_repo: FromDishka[services.UserRepo],
        token_repo: FromDishka[services.TokenRepo],
    ) -> litestar.Response[domain.User]:
        """Custom /refresh endpoint"""
        user = await user_repo.read_user(request.user.id)
        if user is None:
            raise NotAuthorizedException(detail="user no longer exists")
        if request.auth.jti is not None:
            await token_repo.unban(request.auth.jti)
        return oauth2.login(
            identifier=user.id.hex,
            response_body=user,
            token_issuer="backcat",
            token_audience="backcat",
            token_unique_jwt_id=uuid4().hex,
        )

    @litestar.post("/sign-out")
    @inject
    async def signout(
        self,
        request: litestar.Request[domain.User, Token, Any],
        oauth2: FromDishka[OAuth2PasswordBearerAuth[domain.User]],
        token_repo: FromDishka[services.TokenRepo],
    ) -> litestar.Response[None]:
        """Custom /sign-out endpoint"""
        if request.auth.jti is not None:
            await token_repo.ban(request.auth.jti)
        return litestar.Response(headers={"Authorization": ""}, content=None)

    @litestar.get("/me", return_dto=dto.UserProfileResponse)
    @inject
    async def profile(self, *, request: litestar.Request[Any, Token, Any]) -> domain.User:
        return request.user

    @litestar.patch("/me", dto=dto.UpdateUserRequest, return_dto=dto.UpdateUserResponse)
    @inject
    async def update(
        self,
        data: DTOData[domain.User],
        request: litestar.Request[domain.User, Token, Any],
        user_repo: FromDishka[services.UserRepo],
    ) -> domain.User:
        return await user_repo.update_user(
            request.user.id,
            services.user_repo.UpdateUser.model_validate(data.as_builtins()),
        )
