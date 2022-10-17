import operator
from functools import reduce
from typing import Any, Callable

from lark import Lark, Token  # type: ignore
from lark import Transformer as LarkTransformer  # type: ignore

#
# Grammar
#
filter_grammar = r"""
start: filter

filter : [expression]

expression : sequence (_WS+ _AND _WS+ sequence)*

sequence : factor (_WS+ factor)*

factor : term (_WS+ _OR _WS+ term)*

term : [(NOT _WS+ | MINUS)] simple

simple : restriction
       | composite

restriction : comparable [_WS? comparator _WS? arg]

comparable : member
           | function

member : reference

function : reference _LPAREN [_WS? arg_list _WS?] _RPAREN

reference : variable getitem? (getattr getitem?)*

variable : IDENTIFIER

attribute : IDENTIFIER

getattr : _DOT attribute

getitem : _LBRACKET arg _RBRACKET

comparator : EQUALS
           | NOT_EQUALS
           | LESS_THAN
           | LESS_EQUALS
           | GREATER_THAN
           | GREATER_EQUALS
           | HAS

composite : _LPAREN expression _RPAREN

arg_list : arg ( _COMMA _WS? arg )*

arg : comparable
    | composite
    | literal

NOT.99: "NOT"
_AND.99: "AND"
_OR.99: "OR"

_WS: " "

MINUS: "-"
_DOT: "."
_COMMA: ","

_LPAREN: "("
_RPAREN: ")"
_LBRACKET: "["
_RBRACKET: "]"

EQUALS: "="
NOT_EQUALS: "!="
LESS_THAN: "<"
LESS_EQUALS: "<="
GREATER_THAN: ">"
GREATER_EQUALS: ">="
HAS: ":"

IDENTIFIER: /[a-zA-Z_]+[a-zA-Z0-9_]*/

literal.1: int
         | float
         | boolean
         | string

int: /[+-]?\d+/
float: /[+-]?((\d+\.\d+|\d+\.|\.\d+|\d+)([eE][+-]?\d*)|(\d+\.\d+|\d+\.|\.\d+))/
boolean: /True|False/
string: /("|')((?:\\\1|(?:(?!\1).))*)\1/
"""


#
# Converter
#
class Converter:
    def __init__(
        self,
        objects: dict[str, Any],
        getattr: Callable[[Any, Any], Any] = getattr,
        getitem: Callable[[Any, Any], Any] = operator.getitem,
        not_: Callable[[Any], Any] = operator.inv,
        and_: Callable[[Any, Any], Any] = operator.and_,
        or_: Callable[[Any, Any], Any] = operator.or_,
        eq: Callable[[Any, Any], Any] = operator.eq,
        ne: Callable[[Any, Any], Any] = operator.ne,
        lt: Callable[[Any, Any], Any] = operator.lt,
        le: Callable[[Any, Any], Any] = operator.le,
        gt: Callable[[Any, Any], Any] = operator.gt,
        ge: Callable[[Any, Any], Any] = operator.ge,
        has: Callable[[Any, Any], Any] = operator.contains,
    ) -> None:
        self._parser = Lark(filter_grammar)
        self._transformer = Transformer(
            objects=objects,
            getattr=getattr,
            getitem=getitem,
            not_=not_,
            and_=and_,
            or_=or_,
            eq=eq,
            ne=ne,
            lt=lt,
            le=le,
            gt=gt,
            ge=ge,
            has=has,
        )

    def convert(self, query: str):
        tree = self._parser.parse(query)
        return self._transformer.transform(tree)


#
# Transformer
#
class Transformer(LarkTransformer[Token, Any]):
    def __init__(
        self,
        objects: dict[str, Any],
        getattr: Callable[[Any, Any], Any] = getattr,
        getitem: Callable[[Any, Any], Any] = operator.getitem,
        not_: Callable[[Any], Any] = operator.inv,
        and_: Callable[[Any, Any], Any] = operator.and_,
        or_: Callable[[Any, Any], Any] = operator.or_,
        eq: Callable[[Any, Any], Any] = operator.eq,
        ne: Callable[[Any, Any], Any] = operator.ne,
        lt: Callable[[Any, Any], Any] = operator.lt,
        le: Callable[[Any, Any], Any] = operator.le,
        gt: Callable[[Any, Any], Any] = operator.gt,
        ge: Callable[[Any, Any], Any] = operator.ge,
        has: Callable[[Any, Any], Any] = operator.contains,
    ) -> None:
        super().__init__(visit_tokens=True)
        self._objects = objects
        self._getattr = getattr
        self._getitem = getitem
        self._not = not_
        self._and = and_
        self._or = or_
        self._eq = eq
        self._ne = ne
        self._lt = lt
        self._le = le
        self._gt = gt
        self._ge = ge
        self._has = has

    def start(self, t: Any):
        return t[0]

    def filter(self, t: Any):
        if t:
            return t[0]
        return None

    def expression(self, t: Any):
        return reduce(self._and, t)

    def sequence(self, t: Any):
        return reduce(self._and, t)

    def factor(self, t: Any):
        return reduce(self._or, t)

    def term(self, t: Any):
        [not_, simple] = t
        if not_:
            return not_(simple)
        return simple

    def simple(self, t: Any):
        return t[0]

    def restriction(self, t: Any):
        [obj, comparator, arg] = t
        if comparator and arg:
            return comparator(obj, arg)
        return obj

    def comparable(self, t: Any):
        return t[0]

    def member(self, t: Any):
        return t[0]

    def function(self, t: Any):
        func, args = t
        return func(*args)

    def reference(self, t: Any):
        variable, *cs = t
        result = self._objects[variable]
        for c in cs:
            result = c(result)
        return result

    def variable(self, t: Any):
        return t[0]

    def attribute(self, t: Any):
        return t[0]

    def getattr(self, t: Any):
        name = t[0]

        def wrap(obj: Any):
            return self._getattr(obj, name)

        return wrap

    def getitem(self, t: Any):
        key = t[0]

        def wrap(obj: Any):
            return self._getitem(obj, key)

        return wrap

    def comparator(self, t: Any):
        return t[0]

    def composite(self, t: Any):
        return t[0]

    def arg_list(self, t: Any):
        return t

    def arg(self, t: Any):
        return t[0]

    def NOT(self, _: Any):
        return self._not

    def MINUS(self, _: Any):
        return self._not

    def EQUALS(self, _: Any):
        return self._eq

    def NOT_EQUALS(self, _: Any):
        return self._ne

    def LESS_THAN(self, _: Any):
        return self._lt

    def LESS_EQUALS(self, _: Any):
        return self._le

    def GREATER_THAN(self, _: Any):
        return self._gt

    def GREATER_EQUALS(self, _: Any):
        return self._ge

    def HAS(self, _: Any):
        return self._has

    def IDENTIFIER(self, t: Any):
        return str(t)

    def literal(self, t: Any):
        return t[0]

    def int(self, t: Any):
        return int(t[0])

    def float(self, t: Any):
        return float(t[0])

    def boolean(self, t: Any):
        return True if t[0] == "True" else False

    def string(self, t: Any):
        return t[0][1:-1]
