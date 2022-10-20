from dataclasses import dataclass
from uuid import UUID
from ..domain.book import Book
from ..domain.publisher import Publisher
from ..port.repository import IBookRepository, IPublisherRepository

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select


@dataclass
class BookRepository(IBookRepository):

    _session: AsyncSession

    async def add(self, book: Book) -> None:
        self._session.add(book)

    async def get(self, book_id: UUID) -> Book | None:
        return await self._session.get(Book, book_id)

    async def query(self, select: Select) -> list[Book]:
        return (await self._session.execute(select)).scalars().all()

    async def delete(self, book: Book) -> None:
        await self._session.delete(book)


@dataclass
class PublisherRepository(IPublisherRepository):

    _session: AsyncSession

    async def add(self, publisher: Publisher) -> None:
        self._session.add(publisher)

    async def get(self, publisher_id: UUID) -> Publisher | None:
        return await self._session.get(Publisher, publisher_id)

    async def query(self, select: Select) -> list[Publisher]:
        return (await self._session.execute(select)).scalars().all()

    async def delete(self, publisher: Publisher) -> None:
        await self._session.delete(publisher)