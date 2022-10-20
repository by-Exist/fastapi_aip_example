import base64
from typing import Any, Generic, TypeVar, cast

from pydantic import BaseModel
from pydantic.generics import GenericModel
from sqlalchemy import Column, and_, or_, tuple_
from sqlalchemy.sql.elements import ClauseElement, UnaryExpression
from sqlalchemy.sql.operators import asc_op, desc_op
from sqlalchemy.sql.selectable import GenerativeSelect


#
# PageToken
#
class Cursor(BaseModel):
    class Config:
        orm_mode = True


C = TypeVar("C", bound=Cursor)


class PageToken(GenericModel, Generic[C]):
    filter_query: str | None
    order_by_query: str | None
    cursor: C

    def encode(self):
        return base64.urlsafe_b64encode(self.json().encode("utf-8")).decode("utf-8")

    @classmethod
    def decode(cls, page_token: str):
        return cls.parse_raw(base64.urlsafe_b64decode(page_token))


def _get_order_by_clauses(
    selectable: GenerativeSelect,
) -> tuple[Column[Any] | UnaryExpression[Any]]:
    return selectable._order_by_clause.clauses  # type: ignore


def _get_column(clause: Any) -> Column[Any]:
    while hasattr(clause, "element"):
        clause = clause.element
    return clause


def _is_asc(order_clause: ClauseElement) -> bool:
    modifier: Any = getattr(order_clause, "modifier", None)
    if modifier:
        if modifier is asc_op:
            return True
        if modifier is desc_op:
            return False
    element: Any = getattr(order_clause, "element", None)
    if element is None:
        return True
    return _is_asc(element)


# https://stackoverflow.com/questions/38017054/mysql-cursor-based-pagination-with-multiple-columns
def get_page_clause(order_by_clauses: list[Any], cursor: Cursor) -> Any | None:
    result = None
    for clause in reversed(order_by_clauses):
        is_asc = _is_asc(clause)
        column = _get_column(clause)
        column.key = cast(str, column.key)
        value = getattr(cursor, column.key)
        include_clause = column >= value if is_asc else column <= value
        exclude_clause = column > value if is_asc else column < value
        if result is None:
            result = exclude_clause
            continue
        result = and_(include_clause, or_(exclude_clause, tuple_(result)))  # type: ignore
    return result
