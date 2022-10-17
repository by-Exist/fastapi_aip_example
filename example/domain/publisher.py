from dataclasses import dataclass, field
from uuid import UUID


@dataclass(kw_only=True)
class Publisher:

    id: UUID
    title: str

    _version_number: int = field(default=0)
