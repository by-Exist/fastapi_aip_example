import uuid
from typing import Any

from sqlalchemy import Column, Integer, String, Table
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import registry
from sqlalchemy.types import CHAR, TypeDecorator

from ..domain.book import Book
from ..domain.publisher import Publisher


class Uuid(TypeDecorator[Any]):
    """Platform-independent UUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect: Any):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


mapper_registry = registry()


publisher_table = Table(
    "publishers",
    mapper_registry.metadata,
    Column("id", Uuid, primary_key=True),
    Column("title", String(100)),
    Column("_version_number", Integer, nullable=False),
)


book_table = Table(
    "books",
    mapper_registry.metadata,
    Column("id", Uuid, primary_key=True),
    Column("publisher_id", Uuid),
    Column("title", String(100)),
    Column("author_name", String(50)),
    Column("_version_number", Integer, nullable=False),
)


def start_mappers():
    mapper_registry.map_imperatively(
        Book,
        book_table,
        version_id_col=book_table.c._version_number,
    )
    mapper_registry.map_imperatively(
        Publisher,
        publisher_table,
        version_id_col=publisher_table.c._version_number,
    )
