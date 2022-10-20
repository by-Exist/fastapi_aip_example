from dataclasses import dataclass
from uuid import UUID
from domino.block import IBlock


@dataclass(frozen=True, kw_only=True)
class CreatePublisher(IBlock):
    id: UUID
    title: str


@dataclass(frozen=True, kw_only=True)
class CreateBook(IBlock):
    id: UUID
    publisher_id: UUID

    title: str
    author_name: str


@dataclass(frozen=True, kw_only=True)
class DeleteBook(IBlock):
    id: UUID
