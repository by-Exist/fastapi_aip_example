from dataclasses import dataclass, field
from types import TracebackType
from typing import Callable, Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from typing_extensions import Self

from ..config import settings
from ..port.unit_of_work import IUnitOfWork
from .repository import BookRepository, PublisherRepository

engine = create_async_engine(
    settings.DATABASE_URL,
    future=True,
    echo=True,  # FIXME
    # isolation_level="REPEATABLE READ",  # FIXME
)

Session: Callable[[], AsyncSession] = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)  # type: ignore


@dataclass
class UnitOfWork(IUnitOfWork):

    _session: AsyncSession = field(init=False)
    books: BookRepository = field(init=False)
    publishers: PublisherRepository = field(init=False)

    async def __aenter__(self) -> Self:
        self._session = await Session().__aenter__()
        self.books = BookRepository(self._session)
        self.publishers = PublisherRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await self._session.__aexit__(exc_type, exc_value, traceback)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
