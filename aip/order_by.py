import operator
from typing import Any, Callable

from lark import Lark, Token  # type: ignore
from lark import Transformer as LarkTransformer  # type: ignore

#
# Grammar
#
order_by_grammar = r"""
start: order

order : [expression]

expression : term (_WS? _COMMA _WS? term)*

term : field [_WS+ DESC]

field : reference

reference : variable getitem? (getattr getitem?)*

variable : IDENTIFIER

attribute : IDENTIFIER

getattr : _DOT attribute

getitem : _LBRACKET literal _RBRACKET

_WS: " "

DESC: "desc"
_DOT: "."
_COMMA: ","

_LBRACKET: "["
_RBRACKET: "]"

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
        desc: Callable[[Any], Any] = operator.inv,
    ) -> None:
        self._parser = Lark(order_by_grammar)
        self._transformer = Transformer(
            objects=objects,
            getattr=getattr,
            getitem=getitem,
            desc=desc,
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
        desc: Callable[[Any], Any] = operator.inv,
    ) -> None:
        super().__init__(visit_tokens=True)
        self._objects = objects
        self._getattr = getattr
        self._getitem = getitem
        self._desc = desc

    def start(self, t: Any):
        return t[0]

    def order(self, t: Any):
        if t:
            return t[0]
        return None

    def expression(self, t: Any):
        return t

    def term(self, t: Any):
        [field, desc] = t
        if desc:
            return desc(field)
        return field

    def field(self, t: Any):
        return t[0]

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
            return getattr(obj, name)

        return wrap

    def getitem(self, t: Any):
        key = t[0]

        def wrap(obj: Any):
            return operator.getitem(obj, key)

        return wrap

    def DESC(self, _: Any):
        return self._desc

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
