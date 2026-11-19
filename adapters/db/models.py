from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ShardRow(Base):
    __tablename__ = "shards"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    start_index: Mapped[int] = mapped_column(BigInteger)
    end_index: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    worker_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error: Mapped[str | None] = mapped_column(String(256), nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class HitRow(Base):
    __tablename__ = "hits"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    shard_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("shards.id"), index=True)
    chain: Mapped[str] = mapped_column(String(8))
    address: Mapped[str] = mapped_column(String(128), index=True)
    seed: Mapped[str] = mapped_column(String(512))
    balance: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())