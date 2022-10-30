from typing import Any

import pyarrow as pa
import pyarrow.compute as pc

from lark import Lark, Transformer
from lark.exceptions import UnexpectedToken


grammar = """
?start: expression
expression:  unary_expression | binary_expression | grouped_expression | and_or_expression

grouped_expression: _L_PAREN expression _R_PAREN
and_or_expression: expression and_or_op expression

unary_expression: column unary_op
binary_expression: column binary_op value

column: COLUMN_NAME | DOUBLE_QUOTED_STRING
value: number | SINGLE_QUOTED_STRING | BOOLEAN
number: SIGNED_FLOAT | SIGNED_INT

unary_op: IS_NULL | IS_NOT_NULL
binary_op: EQUAL | NOT_EQUAL | LESS_THAN | GREATER_THAN | LESS_THAN_OR_EQUAL | GREATER_THAN_OR_EQUAL | LIKE | NOT_LIKE
and_or_op: OR | AND

IS_NULL: _WHITESPACE+ IS _WHITESPACE+ NULL _WHITESPACE*
IS_NOT_NULL: _WHITESPACE+ IS _WHITESPACE+ NOT _WHITESPACE+ NULL _WHITESPACE*

NOT:   "not"i
IS:    "is"i
NULL:  "null"i

OR:    _WHITESPACE* ("or"i) _WHITESPACE*
AND:   _WHITESPACE* ("and"i) _WHITESPACE*

_L_PAREN: _WHITESPACE* "(" _WHITESPACE* 
_R_PAREN: _WHITESPACE* ")" _WHITESPACE*

LESS_THAN_OR_EQUAL: _WHITESPACE* "<=" _WHITESPACE*
GREATER_THAN_OR_EQUAL: _WHITESPACE* ">=" _WHITESPACE*
LESS_THAN: _WHITESPACE* "<" _WHITESPACE*
GREATER_THAN: _WHITESPACE* ">" _WHITESPACE*
NOT_LIKE: _WHITESPACE* "!~" _WHITESPACE*
NOT_EQUAL: _WHITESPACE* ( "!=" | "<>" ) _WHITESPACE*
LIKE: _WHITESPACE* ( "~~" | "~" ) _WHITESPACE*
EQUAL: _WHITESPACE* ( "==" | "=" ) _WHITESPACE*

SINGLE_QUOTED_STRING: _SINGLE_QUOTE _STRING_ESC_INNER _SINGLE_QUOTE
DOUBLE_QUOTED_STRING: _DOUBLE_QUOTE _STRING_ESC_INNER _DOUBLE_QUOTE

BOOLEAN: TRUE | FALSE
TRUE: _WHITESPACE* "true"i _WHITESPACE*
FALSE: _WHITESPACE* "false"i _WHITESPACE*

_SINGLE_QUOTE: "'"
_DOUBLE_QUOTE: "\\""

%import common.SIGNED_FLOAT
%import common.SIGNED_INT
%import common.CNAME -> COLUMN_NAME
%import common._STRING_ESC_INNER
%import common.WS -> _WHITESPACE
"""


class TypeTransformer(Transformer):

    def SIGNED_INT(self, tok):
        if tok.value and isinstance(tok.value, str):
            tok = tok.update(value=int(tok))
        return tok

    def SIGNED_FLOAT(self, tok):
        if tok.value and isinstance(tok.value, str):
            tok = tok.update(value=float(tok))
        return tok

    def BOOLEAN(self, tok):
        if tok.value and isinstance(tok.value, str):
            tok = tok.update(value=(str(tok).lower() == "true"))
        return tok

    def SINGLE_QUOTED_STRING(self, tok):
        return tok.update(value=tok.strip("'"))

    def DOUBLE_QUOTED_STRING(self, tok):
        return tok.update(value=tok.strip('"'))


class UnexpectedColumn(UnexpectedToken):
    def _format_expected(self, expected):
        return f"Available COLUMNS are: \n\t {', '.join(expected)}"

    def __str__(self):
        message = f"Unexpected COLUMN \"{self.token.value}\" " \
                  f"at line {self.line}, column {self.column}.\n" \
                  f"{self._format_expected(self.accepts or self.expected)}"

        return message


class UnsupportedOperator(UnexpectedToken):
    def _format_expected(self, expected):
        return f"Supported OPERATORS are: \n\t {', '.join(expected)}"

    def __str__(self):
        message = f"OPERATOR \"{self.token.value}\" " \
                  f"at line {self.line}, column {self.column} is not supported for a given COLUMN.\n" \
                  f"{self._format_expected(self.accepts or self.expected)}"

        return message


class InvalidValue(UnexpectedToken):
    def __str__(self):
        message = f"VALUE \"{self.token.value}\" " \
                  f"at line {self.line}, column {self.column} is not valid for a given COLUMN or OPERATOR"

        return message


UNARY_OPERATORS = {
    "IS_NULL": pc.is_null,
    "IS_NOT_NULL": pc.true_unless_null
}


_BASE_BINARY_OPERATORS = {
    "EQUAL": pc.equal,
    "NOT_EQUAL": pc.not_equal,
    "LESS_THAN": pc.less,
    "LESS_THAN_OR_EQUAL": pc.less_equal,
    "GREATER": pc.greater,
    "GREATER_THAN_OR_EQUAL": pc.greater_equal
}


BINARY_OPERATORS_FOR_COLUMN_TYPES = {
    "bool": {
        "EQUAL": pc.equal,
        "NOT_EQUAL": pc.not_equal,
    },
    "string": {
        **_BASE_BINARY_OPERATORS,
        "LIKE": pc.match_like
    },
    "double": _BASE_BINARY_OPERATORS,
    "int64": _BASE_BINARY_OPERATORS,
    "float": _BASE_BINARY_OPERATORS,
    "datetime": _BASE_BINARY_OPERATORS,
}


AND_OR_OPERATORS = {
    "AND": pc.and_,
    "OR": pc.or_
}



class PyArrowFilterBuilder(Transformer):
    def __init__(self, table: pa.Table):
        super().__init__(visit_tokens=False)

        self._table = table
        self._available_columns = {col: str(table[col].type) for col in table.column_names}

    def unary_op(self, tree):
        return tree[0]

    def binary_op(self, tree):
        return tree[0]

    def and_or_op(self, tree):
        return tree[0]

    def number(self, tree):
        return tree[0]

    def value(self, tree):
        return tree[0]

    def column(self, tree):
        column = tree[0]
        if column.value not in self._available_columns:
            raise UnexpectedColumn(column, list(self._available_columns))

        return column

    def unary_expression(self, tree):
        column = tree[0]
        op = tree[1]

        op_name = op.type
        table_column = self._table[column.value]

        return UNARY_OPERATORS[op_name](table_column)

    def binary_expression(self, tree):
        column = tree[0]
        op = tree[1]
        value = tree[2]

        column_type = self._available_columns[column.value]
        op_name = op.type

        if column_type not in BINARY_OPERATORS_FOR_COLUMN_TYPES:
            raise UnsupportedOperator(op, [])
        if op_name not in BINARY_OPERATORS_FOR_COLUMN_TYPES[column_type]:
            raise UnsupportedOperator(op, BINARY_OPERATORS_FOR_COLUMN_TYPES[column_type].keys())

        func = BINARY_OPERATORS_FOR_COLUMN_TYPES[column_type][op_name]
        table_column = self._table[column.value]

        try:
            return func(table_column, value.value)
        except pa.lib.ArrowNotImplementedError:
            raise InvalidValue(value, None)

    def expression(self, tree):
        return tree[0]

    def grouped_expression(self, tree):
        return tree[0]

    def and_or_expression(self, tree):
        left = tree[0]
        op = tree[1]
        right = tree[2]

        func = AND_OR_OPERATORS[op.type]
        return func(left, right)


filter_parser = Lark(grammar, parser='lalr', transformer=TypeTransformer())


def build_pa_filter(table: pa.Table, filters: str) -> Any:
    filter_builder = PyArrowFilterBuilder(table)

    filters_tree = filter_parser.parse(filters)
    return filter_builder.transform(filters_tree)
