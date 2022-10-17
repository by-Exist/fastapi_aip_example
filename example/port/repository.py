from typing import Optional, Protocol, TypeVar
from uuid import UUID

from sqlalchemy.sql.selectable import Select

from ..domain.book import Book
from ..domain.publisher import Publisher

A = TypeVar("A")
I_contra = TypeVar("I_contra", contravariant=True)
Q_contra = TypeVar("Q_contra", contravariant=True)


class ICollectionOrientedRepository(Protocol[A, I_contra, Q_contra]):
    async def add(self, _aggregate: A) -> None:
        ...

    async def get(self, _id: I_contra) -> Optional[A]:
        ...

    async def query(self, select: Q_contra) -> list[A]:
        ...

    async def delete(self, _aggregate: A) -> None:
        ...


class IPersistenceOrientedRepository(Protocol[A, I_contra, Q_contra]):
    async def save(self, _aggregate: A) -> None:
        ...

    async def get(self, _id: I_contra) -> Optional[A]:
        ...

    async def query(self, select: Q_contra) -> list[A]:
        ...

    async def delete(self, _aggregate: A) -> None:
        ...


IBookRepository = ICollectionOrientedRepository[Book, UUID, Select]
IPublisherRepository = ICollectionOrientedRepository[Publisher, UUID, Select]
