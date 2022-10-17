from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(kw_only=True)
class Book:

    id: UUID
    publisher_id: UUID

    title: str
    author_name: str
    publish_time: datetime

    _version_number: int = field(default=0)
