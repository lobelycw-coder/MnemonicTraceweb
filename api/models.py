import uuid
from datetime import datetime
from sqlalchemy import String, BigInteger, DateTime, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase): ...

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)   # telegram id
    username: Mapped[str | None] = mapped_column(String(64))
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    credits: Mapped[int] = mapped_column(default=0)

class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    mode: Mapped[str] = mapped_column(String(16))        # biased | replay | target
    shard: Mapped[str] = mapped_column(String(64))
    rate: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(16), default="queued")
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Hit(Base):
    __tablename__ = "hits"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id"))
    mnemonic: Mapped[str] = mapped_column(String(256))    # encrypt before prod
    address: Mapped[str] = mapped_column(String(128))
    chain: Mapped[str] = mapped_column(String(16))
    usd: Mapped[float] = mapped_column(Numeric(18, 8), default=0)
    swept: Mapped[bool] = mapped_column(Boolean, default=False)
    found: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)