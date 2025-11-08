# database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Integer, ForeignKey
from datetime import datetime
from typing import Optional, AsyncGenerator
import logging
from sqlalchemy.sql import func  # Added for default timestamps

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    google_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_pic: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    files: Mapped[list["File"]] = relationship(back_populates="owner")


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    ipfs_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_email: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.email"), nullable=False, index=True
    )
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    owner: Mapped["User"] = relationship(
        back_populates="files", primaryjoin="File.owner_email == User.email"
    )


class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.async_session_maker = None

    async def connect(self, database_url: str):
        """Initialize database connection"""
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        self.async_session_maker = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)

        logger.info("PostgreSQL connected successfully and tables created")

    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            logger.info("PostgreSQL connection closed")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        if not self.async_session_maker:
            raise RuntimeError("Database not initialized. Call connect() first.")

        async with self.async_session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Global database manager instance
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async for session in db_manager.get_session():
        yield session


# Export models for easy import
__all__ = ["db_manager", "get_db", "User", "File", "Base"]