#
# PartCAD, 2026
#
# Licensed under Apache License, Version 2.0.
#
"""PartCAD's own expression syntax, ``%<expression>%``.

Jinja2 owns ``{{ ... }}`` and ``{% ... %}`` in ``partcad.yaml``: the file is
rendered as a template *before* it is parsed (see 'ProjectLocal'), so anything
written that way is resolved at load time, where the parameter values of an
individual object do not exist yet. An expression that has to wait for those
values therefore cannot be spelled in Jinja2's syntax at all - it would be
evaluated, and fail, one step too early.

``%...%`` is what is left. It is not new here: the names in an interface's
``inherits:`` section have been resolved this way since interfaces were
introduced (``%moveX%``, ``%moveX:value*2%``). This module is that mechanism
generalized - the same delimiters, the same evaluation, applied to any string in
a declaration and over the object's own parameters rather than one named one -
and it keeps the two historical spellings working.

Three forms, tried in this order:

* ``%name%`` - the value of the parameter called ``name``, with its own type.
  A location entry written ``"%depth%"`` stays the number it was declared as.
* ``%name:expression%`` - the historical form, where ``name`` is a parameter and
  ``value`` is bound to its value inside ``expression``.
* ``%expression%`` - arithmetic over the object's parameters, e.g. ``%size / 2%``
  or ``%-width / 2 + offset%``. Arithmetic, comparisons and a conditional, and
  nothing else: a declaration is read whenever a package is loaded, long before
  anything is built, so what one may do is checked rather than assumed
  ('_ALLOWED_NODES').

A string that is *exactly* one expression evaluates to the value itself, so a
number stays a number. A string that merely contains one (``"m;size=%size%"``,
``"%depth%mm deep"``) gets the value formatted into it.
"""

import ast
import math
import re
from typing import Any

from . import logging as pc_logging

# Deliberately '[^%]' rather than '[^%*]': the historical pattern in
# 'Interface.instantiate' excluded '*' as well, which quietly made '%a*b%'
# not an expression. There is no reason a product cannot be one.
PATTERN = re.compile(r"%([^%]+)%")

# What an expression may call. '__builtins__' is emptied - an expression in a
# package declaration is not a place to open files from - and what is put back
# is the arithmetic that writing a coordinate actually needs.
SAFE_NAMES: dict[str, Any] = {
    "abs": abs,
    "bool": bool,
    "float": float,
    "int": int,
    "len": len,
    "max": max,
    "min": min,
    "round": round,
    "str": str,
    "acos": math.acos,
    "asin": math.asin,
    "atan": math.atan,
    "atan2": math.atan2,
    "ceil": math.ceil,
    "cos": math.cos,
    "degrees": math.degrees,
    "floor": math.floor,
    "hypot": math.hypot,
    "log": math.log,
    "pow": math.pow,
    "radians": math.radians,
    "sin": math.sin,
    "sqrt": math.sqrt,
    "tan": math.tan,
    "e": math.e,
    "pi": math.pi,
    "PI": math.pi,
    "M_PI": math.pi,
    "INCH": 25.4,
    "INCHES": 25.4,
    "FOOT": 304.8,
    "FEET": 304.8,
}


class ExpressionError(Exception):
    """An expression that could not be evaluated, with the text that failed."""

    def __init__(self, expression: str, cause: Exception):
        self.expression = expression
        self.cause = cause
        super().__init__("failed to evaluate '%%%s%%': %s" % (expression, cause))


def evaluate(expression: str, values: dict[str, Any]) -> Any:
    """The value of one ``%...%`` expression, given the object's parameters."""
    name = expression.strip()
    if name in values:
        # The whole expression is a parameter name: hand the value back as it
        # is, so that a number stays a number and a string stays a string.
        return values[name]

    if ":" in expression:
        # The historical '%name:expression%', where 'value' is the parameter.
        head, _, tail = expression.partition(":")
        head = head.strip()
        if head in values:
            return _eval(tail, {**values, "value": values[head]}, expression)

    return _eval(expression, values, expression)


# What an expression may be made of. Arithmetic, comparisons, a conditional and
# a call to one of the names above - and nothing that reaches for an object's
# insides.
#
# The check is on the syntax tree rather than on the names in scope, because
# emptying '__builtins__' is not by itself a sandbox: '().__class__' walks from
# any literal to every class in the interpreter, so an expression that may write
# an attribute access may do anything at all. A declaration in 'partcad.yaml' is
# read whenever a package is loaded - long before anything is built and any CAD
# script runs - so what it is allowed to do is worth stating rather than
# assuming.
_ALLOWED_NODES = (
    ast.Expression,
    ast.BoolOp,
    ast.BinOp,
    ast.UnaryOp,
    ast.IfExp,
    ast.Compare,
    ast.Call,
    ast.Constant,
    ast.Name,
    ast.Load,
    ast.Tuple,
    ast.List,
    ast.boolop,
    ast.operator,
    ast.unaryop,
    ast.cmpop,
)


def _check(tree: ast.AST, expression: str) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ExpressionError(
                expression,
                SyntaxError("%s is not allowed in an expression" % type(node).__name__),
            )
        if isinstance(node, ast.Call) and not isinstance(node.func, ast.Name):
            raise ExpressionError(expression, SyntaxError("only the built-in functions may be called"))
        if isinstance(node, ast.Call) and (node.keywords or any(isinstance(a, ast.Starred) for a in node.args)):
            raise ExpressionError(expression, SyntaxError("an expression calls with plain arguments only"))


def _eval(expression: str, values: dict[str, Any], reported: str) -> Any:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise ExpressionError(reported, e) from e
    _check(tree, reported)
    try:
        return eval(  # nosec B307 - checked above, no builtins, only the object's own parameters
            compile(tree, "<partcad expression>", "eval"),
            {"__builtins__": {}, **SAFE_NAMES},
            dict(values),
        )
    except Exception as e:
        raise ExpressionError(reported, e) from e


def format_value(value: Any) -> str:
    """How an evaluated value reads when it is put back into a string.

    A whole number loses its fraction, because these values end up in *names*:
    a size of 3.0 asks for the sketch 'm;size=3', which is the same instance
    'm;size=3' asked for by hand, while 'm;size=3.0' would be a second one.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return repr(value)
    return str(value)


def substitute(text: str, values: dict[str, Any]) -> Any:
    """Resolve every ``%...%`` in one string.

    A string that is nothing but an expression evaluates to the value itself -
    that is what lets a coordinate be written ``"%size / 2%"`` and still be a
    number. Anything else is a string with the values formatted into it.
    """
    whole = PATTERN.fullmatch(text)
    if whole is not None:
        return evaluate(whole.group(1), values)
    return PATTERN.sub(lambda m: format_value(evaluate(m.group(1), values)), text)


def has_expression(value: Any) -> bool:
    """Whether anything in this value carries a ``%...%`` at all."""
    if isinstance(value, str):
        return PATTERN.search(value) is not None
    if isinstance(value, dict):
        return any(has_expression(k) or has_expression(v) for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return any(has_expression(item) for item in value)
    return False


def resolve(value: Any, values: dict[str, Any], where: str = "") -> Any:
    """Resolve the expressions everywhere inside a declaration.

    Walks strings, lists and dictionaries - keys included, so that a parametrized
    reference can be the *name* of an inherited interface - and leaves everything
    else alone. An expression that cannot be evaluated is reported and left
    standing as the text it was written as: a package that misspells one loses
    that one value rather than failing to load, and the message names the
    expression rather than whatever the unresolved text later fails to be.
    """
    if isinstance(value, str):
        if PATTERN.search(value) is None:
            return value
        try:
            return substitute(value, values)
        except ExpressionError as e:
            pc_logging.error("%s%s" % (where + ": " if where else "", e))
            return value
    if isinstance(value, dict):
        return {resolve(k, values, where): resolve(v, values, where) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(item, values, where) for item in value]
    return value
