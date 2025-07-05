from uuid import UUID

from sqlalchemy.orm import Mapped

from .base import BaseModel


class ProductImageModel(BaseModel):
    __tablename__ = "product_image"

    hash: Mapped[str]  # noqa: VNE003
    priority: Mapped[int]
    product_id: Mapped[UUID]
