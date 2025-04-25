from uuid import UUID

from sqlalchemy.orm import Mapped

from .base import BaseModel


class ProductImageModel(BaseModel):
    __tablename__ = "product_image"

    hash: Mapped[str]  # noqa: VNE003
    image: Mapped[str]
    priority: Mapped[int]
    product_id: Mapped[UUID]


class ProductImageProcessedModel(BaseModel):
    __tablename__ = "product_image_processed"

    image: Mapped[str]
    width: Mapped[int]
    height: Mapped[int]
    original_image_id: Mapped[UUID]
