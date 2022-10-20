from dataclasses import dataclass
from uuid import UUID
from domino.block import IBlock


@dataclass(frozen=True, kw_only=True)
class PublisherCreated(IBlock):
    id: UUID


@dataclass(frozen=True, kw_only=True)
class BookCreated(IBlock):
    id: UUID


@dataclass(frozen=True, kw_only=True)
class BookDeleted(IBlock):
    id: UUID
