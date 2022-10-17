from abc import abstractmethod
from typing import Protocol

from typing_extensions import Self


# Block
class IBlock(Protocol):
    ...


class IPublicBlock(IBlock, Protocol):
    @abstractmethod
    def to_json(self) -> str:
        ...


class IExternalBlock(IBlock, Protocol):
    @abstractmethod
    async def fall_down(self) -> list[IBlock]:
        ...

    @classmethod
    @abstractmethod
    def from_json(cls, json: str) -> Self:
        ...
