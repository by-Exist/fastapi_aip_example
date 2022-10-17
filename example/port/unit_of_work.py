from types import TracebackType
from typing import Optional, Protocol

from typing_extensions import Self
from .repository import IPublisherRepository, IBookRepository


class IContextManagerUnitOfWork(Protocol):
    async def __aenter__(self) -> Self:
        ...

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        ...

    async def commit(self) -> None:
        ...

    async def rollback(self) -> None:
        ...


class IUnitOfWork(IContextManagerUnitOfWork, Protocol):

    books: IBookRepository
    publishers: IPublisherRepository
