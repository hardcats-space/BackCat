from typing import Annotated, Any

import litestar
from dishka.integrations.litestar import FromDishka, inject
from litestar.dto import DTOData
from litestar.exceptions import NotFoundException
from litestar.params import Parameter

from backcat import domain, services
from backcat.cmd.server.api.v1.review import dto


class Controller(litestar.Controller):
    path = "/review"
    tags = ["review"]

    @litestar.post("", dto=dto.CreateReviewRequest, return_dto=dto.CreateReviewResponse)
    @inject
    async def create(
        self,
        area_id: Annotated[domain.AreaID, Parameter(query="areaId")],
        data: DTOData[domain.Review],
        request: litestar.Request[domain.User, Any, Any],
        review_repo: FromDishka[services.ReviewRepo],
    ) -> domain.Review:
        return await review_repo.create_review(
            request.user.id,
            data.create_instance(**domain.Review.new_defaults_kwargs()),
            area_id,
        )

    @litestar.get("/{id:uuid}", return_dto=dto.ReadReviewResponse)
    @inject
    async def read_one(
        self,
        id: domain.ReviewID,
        request: litestar.Request[domain.User, Any, Any],
        review_repo: FromDishka[services.ReviewRepo],
    ) -> domain.Review:
        review = await review_repo.read_review(request.user.id, id)
        if review is None:
            raise NotFoundException(detail="review not found")
        return review

    @litestar.get("", return_dto=dto.ReadManyReviewResponse)
    @inject
    async def read_many(
        self,
        area_id: Annotated[domain.AreaID, Parameter(query="areaId")],
        request: litestar.Request[domain.User, Any, Any],
        review_repo: FromDishka[services.ReviewRepo],
    ) -> dto._ReadManyReviews:
        return dto._ReadManyReviews(
            data=await review_repo.filter_review(
                request.user.id,
                services.review_repo.FilterReview(area_id=area_id),
            )
        )

    @litestar.patch("/{id:uuid}", dto=dto.UpdateReviewRequest, return_dto=dto.UpdateReviewResponse)
    @inject
    async def update(
        self,
        id: domain.ReviewID,
        data: DTOData[domain.Review],
        request: litestar.Request[domain.User, Any, Any],
        review_repo: FromDishka[services.ReviewRepo],
    ) -> domain.Review:
        return await review_repo.update_review(
            request.user.id,
            id,
            services.review_repo.UpdateReview.model_validate(data.as_builtins()),
        )

    @litestar.delete("/{id:uuid}")
    @inject
    async def delete(
        self,
        id: domain.ReviewID,
        request: litestar.Request[domain.User, Any, Any],
        review_repo: FromDishka[services.ReviewRepo],
    ) -> None:
        await review_repo.delete_review(request.user.id, id)
