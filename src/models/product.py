from uuid import UUID

from sqlalchemy.orm import Mapped

from models.base import BaseModel


class ProductModel(BaseModel):
    __tablename__ = "product"

    active: Mapped[bool]
    owner_id: Mapped[UUID]
