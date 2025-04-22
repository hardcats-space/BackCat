import litestar
from litestar.dto import DTOData

from backcat import domain
from backcat.cmd.server.api.v1.review import dto


class Controller(litestar.Controller):
    path = "/review"

    @litestar.post("", dto=dto.CreateReviewRequest, return_dto=dto.CreateReviewResponse)
    async def create(self, data: DTOData[domain.Review], area_id: domain.AreaID) -> domain.Review:
        return domain.review.ReviewFactory.build()

    @litestar.get("/{id:uuid}", return_dto=dto.ReadReviewResponse)
    async def read_one(self, id: domain.ReviewID) -> domain.Review:
        return domain.review.ReviewFactory.build()

    @litestar.get("", return_dto=dto.ReadManyReviewResponse)
    async def read_many(self, area_id: domain.AreaID) -> dto._ReadManyReviews:
        return dto._ReadManyReviews(data=[domain.review.ReviewFactory.build() for i in range(3)])

    @litestar.patch("/{id:uuid}", dto=dto.UpdateReviewRequest, return_dto=dto.UpdateReviewResponse)
    async def update(self, id: domain.ReviewID, data: DTOData[domain.Review]) -> domain.Review:
        return domain.review.ReviewFactory.build()

    @litestar.delete("/{id:uuid}")
    async def delete(self, id: domain.ReviewID) -> None:
        return None
