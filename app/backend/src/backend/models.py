"""ORM models. Kept intentionally tiny for the lab."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Run(Base):
    __tablename__ = "runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    best_model: Mapped[str] = mapped_column(String(64), nullable=False)
    wrmse: Mapped[float] = mapped_column(Float, nullable=False)
    source_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="stub")
    source_file: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "nombre": self.nombre,
            "best_model": self.best_model,
            "wrmse": self.wrmse,
            "source_mode": self.source_mode,
            "source_file": self.source_file,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
