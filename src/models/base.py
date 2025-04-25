from typing import Annotated
from uuid import UUID

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid6 import uuid7

uuid_pk = Annotated[UUID, mapped_column(primary_key=True, default=uuid7)]


class BaseModel(DeclarativeBase):
    id: Mapped[uuid_pk]  # noqa: VNE003
