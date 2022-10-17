from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from domino.block import IBlock


@dataclass(frozen=True, kw_only=True)
class CreatePublisher(IBlock):
    id: UUID
    title: str


@dataclass(frozen=True, kw_only=True)
class FixPublisherTitle(IBlock):
    id: UUID
    new_title: str


@dataclass(frozen=True, kw_only=True)
class CreateBook(IBlock):
    id: UUID
    publisher_id: UUID

    title: str
    author_name: str
    publish_time: datetime


@dataclass(frozen=True, kw_only=True)
class DeleteBook(IBlock):
    id: UUID
