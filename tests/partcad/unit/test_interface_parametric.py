#!/usr/bin/env python3
#
# PartCAD, 2026
#
# Licensed under Apache License, Version 2.0.
#
"""Interfaces and ports parametrized the way parts and sketches are.

The subject is one package, 'data/parametric_interfaces', which declares the
metric fastener family once instead of once per size: what used to take a
Jinja2 loop over every size, depth and width a package might ever be asked for
is a handful of declarations with 'variables:' on them.
"""

from unittest import mock

import pytest

import partcad as pc
from partcad import expr

PACKAGE = "tests/partcad/unit/data/parametric_interfaces/partcad.yaml"


@pytest.fixture
def ctx():
    # A context of its own rather than 'pc.init()', which hands back the
    # process-wide one when the path matches: these tests read what resolving
    # an interface put into the context, and a context another test has already
    # walked would answer for that test instead.
    return pc.Context(PACKAGE)


# --- the expression syntax itself -------------------------------------------


def test_expression_whole_string_keeps_the_type():
    """A coordinate written as an expression is a number, not the text of one."""
    assert expr.substitute("%size%", {"size": 4.0}) == 4.0
    assert expr.substitute("%size / 2%", {"size": 5.0}) == 2.5
    assert expr.substitute("%-pitch / 2%", {"pitch": 31.0}) == -15.5


def test_expression_inside_a_string_is_formatted_into_it():
    assert expr.substitute("%depth%mm deep", {"depth": 4.0}) == "4mm deep"
    assert expr.substitute("m;size=%size%", {"size": 2.5}) == "m;size=2.5"
    assert expr.substitute("%a% by %b%", {"a": 1.0, "b": 2}) == "1 by 2"


def test_expression_may_use_arithmetic_and_math():
    values = {"size": 9.0}
    assert expr.substitute("%sqrt(size)%", values) == 3.0
    assert expr.substitute("%max(size, 10)%", values) == 10
    assert expr.substitute("%round(size / 2)%", values) == 4


@pytest.mark.parametrize(
    "expression",
    [
        "%open('/etc/passwd')%",  # no builtins
        "%().__class__%",  # and no way to walk to them
        "%size.__class__%",
        "%[x for x in (1, 2)]%",
        "%(lambda: 1)()%",
    ],
)
def test_an_expression_is_arithmetic_and_nothing_else(expression):
    """A declaration is read whenever a package is loaded, long before anything is built."""
    with pytest.raises(expr.ExpressionError):
        expr.substitute(expression, {"size": 4.0})


def test_an_expression_may_be_a_conditional():
    """What is allowed is allowed: comparisons and a conditional are arithmetic."""
    assert expr.substitute("%size if size > 3 else 3%", {"size": 4.0}) == 4.0
    assert expr.substitute("%size if size > 3 else 3%", {"size": 2.0}) == 3


def test_expression_historical_spelling_still_resolves():
    """'%name:expression%', which interface names have used since 2024."""
    assert expr.substitute("%size:value * 2%", {"size": 3.0}) == 6.0


def test_expression_is_not_jinja2():
    """Jinja2's delimiters are left alone: 'partcad.yaml' was rendered already."""
    assert expr.substitute("{{ size }}", {"size": 3.0}) == "{{ size }}"


def test_resolve_walks_keys_and_lists():
    resolved = expr.resolve(
        {"m;size=%size%": [["%-size%", 0, 0], [0, 0, 1], 0]},
        {"size": 4.0},
    )
    assert resolved == {"m;size=4": [[-4.0, 0, 0], [0, 0, 1], 0]}


def test_resolve_reports_a_broken_expression_and_leaves_it():
    """A package that misspells one expression loses that value, not the package."""
    reported = []
    with mock.patch.object(pc.logging, "error", lambda *args: reported.append(args)):
        assert expr.resolve("%nope + 1%", {"size": 4.0}, "//test:iface") == "%nope + 1%"
    assert len(reported) == 1
    assert "%nope + 1%" in str(reported[0])
    assert "//test:iface" in str(reported[0])


# --- referencing a parametrized interface -----------------------------------


def test_interface_is_built_with_the_values_the_reference_names(ctx):
    thru = ctx.get_interface(":m-thru;size=4,depth=2")
    assert thru is not None
    assert thru.desc == "2mm thick through hole of 4mm diameter"
    assert thru.info()["variables"] == {"size": 4.0, "depth": 2.0}


def test_interface_defaults_apply_when_nothing_is_named(ctx):
    thru = ctx.get_interface(":m-thru")
    assert thru.desc == "3mm thick through hole of 3mm diameter"


def test_the_same_values_are_the_same_interface(ctx):
    """Whatever order they are written in, and however the numbers are spelled.

    An interface's name is what a mating is registered under, so two objects
    for one set of values would be two halves of a connection that never find
    each other.
    """
    a = ctx.get_interface(":m-thru;size=4,depth=2")
    b = ctx.get_interface(":m-thru;depth=2,size=4")
    c = ctx.get_interface(":m-thru;depth=2.0,size=4.00")
    assert a is b is c
    assert a.full_name == "//:m-thru;depth=2,size=4"


def test_parameter_values_may_also_be_passed_separately(ctx):
    """What 'pc info -i -p size=4' does."""
    named = ctx.get_interface(":m-thru;size=4,depth=2")
    passed = ctx.get_interface(":m-thru", params={"size": "4", "depth": "2"})
    assert named is passed


def test_an_unparametrized_interface_still_works(ctx):
    plain = ctx.get_interface(":plain")
    assert plain is not None
    assert list(plain.get_ports().keys()) == ["plain"]


def test_a_parameter_the_interface_does_not_declare_is_reported(ctx):
    assert ctx.get_interface(":m-thru;nope=1") is None


def test_an_interface_with_no_variables_cannot_be_parametrized(ctx):
    assert ctx.get_interface(":plain;size=4") is None


# --- what the values reach ---------------------------------------------------


def test_a_port_passes_its_parameter_values_to_its_sketch(ctx):
    """One sketch serves the family, instead of one sketch per size."""
    port = ctx.get_interface(":m-thru;size=4,depth=2").get_ports()["thru-opening-m"]
    assert port.sketch.name == "m;size=4"
    assert port.sketch.info()["outline"] == {"circle": 2.0}

    # A value equal to the default still names an instance of its own, exactly
    # as 'cube;width=10' does where 10 is what 'cube' defaults to.
    port3 = ctx.get_interface(":m-thru;size=3,depth=2").get_ports()["thru-opening-m"]
    assert port3.sketch.name == "m;size=3"
    assert port3.sketch.info()["outline"] == {"circle": 1.5}


def test_port_coordinates_may_be_expressions(ctx):
    pattern = ctx.get_interface(":m-square-pattern;size=4,pitch=20,depth=2")
    corners = {name: port.location.as_packed()[0] for name, port in pattern.get_ports().items()}
    assert corners == {
        "TL-thru-opening-m": [-10.0, 10.0, 0.0],
        "TR-thru-opening-m": [10.0, 10.0, 0.0],
        "BL-thru-opening-m": [-10.0, -10.0, 0.0],
        "BR-thru-opening-m": [10.0, -10.0, 0.0],
    }


def test_an_inherited_interface_may_be_named_by_an_expression(ctx):
    pattern = ctx.get_interface(":m-square-pattern;size=4,pitch=20,depth=2")
    assert sorted(pattern.get_parents().keys()) == ["//:m-thru;depth=2,size=4"]


def test_freedom_of_movement_may_be_an_expression(ctx):
    """'parameters:' still means the freedom of movement, and reads the values."""
    screw = ctx.get_interface(":m-screw;size=4,length=10")
    assert screw.params["moveZ"].max == 8.0
    assert ctx.get_interface(":m-screw;size=4,length=6").params["moveZ"].max == 4.0


def test_an_interface_narrows_the_freedom_it_inherits(ctx):
    """The screw's own 'moveZ' is how far this screw goes in, not 'm's silence."""
    screw = ctx.get_interface(":m-screw;size=4,length=10")
    screw.test()  # the inherited parameters arrive when the interface is instantiated
    assert screw.params["moveZ"].max == 8.0
    # And what it does not redeclare it still gets: 'm' allows the full turn.
    assert screw.params["turnZ"].max == 360


def test_anything_else_of_an_interface_may_be_an_expression(ctx):
    assert ctx.get_interface(":m;size=5").get_thread_step() == 1.0


def test_mates_are_registered_between_the_parametrized_instances(ctx):
    thru = ctx.get_interface(":m-thru;size=4,depth=2")
    thru.test()  # 'mates:' is read when the interface is instantiated, which is lazy
    assert list(ctx.mates.get(thru.full_name, {}).keys()) == ["//:m-screw;size=4"]
    # And the other way round, which is what makes the screw find the hole.
    screw = ctx.get_interface(":m-screw;size=4")
    assert thru.full_name in ctx.mates.get(screw.full_name, {})


# --- a shape's own ports and the interfaces it implements --------------------


def test_a_part_implements_an_interface_parametrized_by_its_own_parameters(ctx):
    plate = ctx.get_part(":plate")
    assert "//:m-thru;depth=3,size=3" in plate.with_ports.get_interfaces()

    thicker = ctx.get_part(":plate;thickness=5")
    assert "//:m-thru;depth=5,size=3" in thicker.with_ports.get_interfaces()


def test_a_part_gets_the_ports_of_the_interface_it_implements(ctx):
    plate = ctx.get_part(":plate")
    assert sorted(plate.with_ports.get_ports().keys()) == [
        "BL-thru-opening-m",
        "BR-thru-opening-m",
        "TL-thru-opening-m",
        "TR-thru-opening-m",
    ]
