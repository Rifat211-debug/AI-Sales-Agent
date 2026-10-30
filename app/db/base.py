from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import DateTime
from sqlalchemy import func

from datetime import datetime


class Base(DeclarativeBase):
    """Base class for all declarative models."""
    pass


class TimeStampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True), server_default = func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone = True), server_default = func.now()
    )