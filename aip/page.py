import base64
from typing import Any, Generic, TypeVar, cast

from pydantic import BaseModel
from pydantic.generics import GenericModel
from sqlalchemy import Column, and_, or_, tuple_
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import UnaryExpression
from sqlalchemy.sql.operators import asc_op, desc_op


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


def _is_asc(order_clause: Any) -> bool:
    modifier = getattr(order_clause, "modifier", None)
    if modifier is not None:
        if modifier is asc_op:
            return True
        if modifier is desc_op:
            return False
    el = getattr(order_clause, "element", None)
    if el is None:
        return True
    return _is_asc(el)


# https://stackoverflow.com/questions/38017054/mysql-cursor-based-pagination-with-multiple-columns
def get_page_clause(order_clauses: list[Any], cursor: Cursor) -> Any:
    result = None
    for clause in reversed(order_clauses):
        is_asc = _is_asc(clause)
        column: Column[Any]
        if isinstance(clause, InstrumentedAttribute):
            column = clause.expression  # type: ignore
        elif isinstance(clause, UnaryExpression):
            column = clause.element  # type: ignore
        else:
            column = clause
        column.key = cast(str, column.key)
        cursor_value = getattr(cursor, column.key)
        include_clause = column >= cursor_value if is_asc else column <= cursor_value
        exclude_clause = column > cursor_value if is_asc else column < cursor_value
        if result is None:
            result = exclude_clause
            continue
        result = and_(include_clause, or_(exclude_clause, tuple_(result)))  # type: ignore
    return result
