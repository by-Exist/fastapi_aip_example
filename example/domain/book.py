from dataclasses import dataclass, field
from uuid import UUID


@dataclass(kw_only=True)
class Book:

    id: UUID
    publisher_id: UUID

    title: str
    author_name: str

    _version_number: int = field(default=0)
