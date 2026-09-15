#
# PartCAD, 2026
#
# Licensed under Apache License, Version 2.0.
#
"""Which layers of a drawing a sketch reads is a parameter, not just a field.

A DXF holds the outline of a part and the lines its bends go along, on layers of
its own. Before this, which of them a sketch read was a field of the
declaration, so reading two of them meant declaring a second sketch - and a
third for the next combination somebody wanted.

They are object-type parameters now: 'include' and 'exclude' are contributed by
the 'dxf' type itself rather than invented by the author of the sketch, so they
exist whether or not the declaration mentions them, and whoever *refers* to the
sketch can set them: 'bends;include=BEND_UP,BEND_DOWN'. The top-level fields
stay exactly what they were, as the default the reference overrides.

Nothing here builds a sketch: what is checked is which layers the factory is
left holding, which is settled while the package is loaded.
"""

import pytest
import yaml

import partcad as pc
from partcad.factory import ObjectTypeParameterException
from partcad.sketch_factory_dxf import SketchFactoryDxf
from partcad.utils import format_parameterized_name, parse_parameterized_name


def _package(tmp_path, sketches):
    (tmp_path / "partcad.yaml").write_text(yaml.safe_dump({"name": "//test", "sketches": sketches}))
    for name, sketch in sketches.items():
        (tmp_path / (sketch.get("path") or (name + ".dxf"))).write_text("")
    return pc.Context(str(tmp_path))


def _layers(sketch, name):
    """The layers the DXF factory reads for this sketch, by its own rule."""
    return SketchFactoryDxf.layers(sketch.config, name)


#
# What a declaration says
#


def test_the_top_level_fields_are_the_declared_default(tmp_path):
    """'include:'/'exclude:' go on meaning exactly what they always meant."""
    ctx = _package(
        tmp_path,
        {
            "listed": {"type": "dxf", "include": ["BEND_UP", "BEND_DOWN"]},
            "single": {"type": "dxf", "exclude": "OUTLINE"},
        },
    )
    assert _layers(ctx.get_sketch("//test:listed"), "include") == ["BEND_UP", "BEND_DOWN"]
    assert _layers(ctx.get_sketch("//test:single"), "exclude") == ["OUTLINE"]


def test_a_drawing_with_no_filters_reads_every_layer(tmp_path):
    """Which is what an empty list has always meant here."""
    ctx = _package(tmp_path, {"bends": {"type": "dxf"}})
    sketch = ctx.get_sketch("//test:bends")
    assert _layers(sketch, "include") == []
    assert _layers(sketch, "exclude") == []


def test_the_filters_can_be_declared_as_parameters(tmp_path):
    """The long form, for a sketch that wants to describe its own default."""
    ctx = _package(
        tmp_path,
        {"bends": {"type": "dxf", "parameters": {"include": {"type": "array", "default": ["BEND_UP"]}}}},
    )
    assert _layers(ctx.get_sketch("//test:bends"), "include") == ["BEND_UP"]


#
# What a reference says
#


def test_a_reference_reads_the_layers_it_asks_for(tmp_path):
    """The point of the whole thing: one drawing, read as many ways as needed.

    The sketch declares no parameters at all - the type contributes them - so
    nothing had to be written down in advance for this reference to work.
    """
    ctx = _package(tmp_path, {"bends": {"type": "dxf"}})
    sketch = ctx.get_sketch("//test:bends;include=BEND_UP,BEND_DOWN")
    assert sketch is not None
    assert _layers(sketch, "include") == ["BEND_UP", "BEND_DOWN"]

    # ...and the sketch it asked for is a different sketch from the one that
    # reads everything, which is what keeps the two from sharing a cache entry.
    assert sketch.name != "bends"
    assert sketch.hash.get() != ctx.get_sketch("//test:bends").hash.get()


def test_a_reference_outranks_the_declared_default(tmp_path):
    """Whoever refers to a sketch is the outer of the two, as everywhere else."""
    ctx = _package(tmp_path, {"bends": {"type": "dxf", "include": ["OUTLINE"]}})
    assert _layers(ctx.get_sketch("//test:bends;include=BEND_UP"), "include") == ["BEND_UP"]


def test_a_name_carries_more_than_one_list(tmp_path):
    """Two parameters, each a list, in one name - the parsing that needs care.

    A real drawing is read with one of the two filters: the importer takes
    'include' or 'exclude' and refuses both, which is CadQuery's rule and not
    this layer's. What is checked here is that a name holding two
    comma-separated values is read back as two values and not as five
    parameters.
    """
    ctx = _package(tmp_path, {"bends": {"type": "dxf"}})
    sketch = ctx.get_sketch("//test:bends;exclude=NOTES,DIMS,include=BEND_UP,BEND_DOWN")
    assert _layers(sketch, "include") == ["BEND_UP", "BEND_DOWN"]
    assert _layers(sketch, "exclude") == ["NOTES", "DIMS"]


def test_a_list_value_survives_being_written_as_a_name():
    """A comma separates parameters, and a list is written with commas in it.

    So a fragment with no '=' continues the value before it. Without that,
    'include=BEND_UP,BEND_DOWN' would parse as a parameter called 'BEND_DOWN' -
    which no object declares, and which used to be rejected moments later.
    """
    assert parse_parameterized_name("bends;include=BEND_UP,BEND_DOWN") == (
        "bends",
        {"include": "BEND_UP,BEND_DOWN"},
    )
    name = format_parameterized_name("bends", {"include": "A,B", "exclude": "C"})
    assert parse_parameterized_name(name) == ("bends", {"include": "A,B", "exclude": "C"})


#
# Which types contribute them
#


def test_a_sketch_type_with_no_layers_rejects_the_parameters(tmp_path, caplog):
    """A layer is a thing a DXF has; an SVG and a script have none.

    Accepted silently, such a parameter would be one the package believed was
    filtering something. It is the per-object failure a rejected part parameter
    is, so the rest of the package goes on loading.
    """
    ctx = _package(
        tmp_path,
        {
            "drawing": {"type": "svg", "path": "drawing.svg", "parameters": {"include": {"type": "array"}}},
            "fine": {"type": "dxf"},
        },
    )
    (tmp_path / "drawing.svg").write_text("")
    with caplog.at_level("ERROR"):
        assert ctx.get_sketch("//test:drawing") is None
    assert "does not accept" in caplog.text
    assert "include" in caplog.text

    # The package is otherwise fine.
    assert ctx.get_sketch("//test:fine") is not None


def test_only_the_registered_names_are_policed(tmp_path):
    """Every other parameter name stays the sketch author's own invention."""
    ctx = _package(
        tmp_path,
        {"drawing": {"type": "svg", "path": "drawing.svg", "parameters": {"included": 1.0}}},
    )
    (tmp_path / "drawing.svg").write_text("")
    assert ctx.get_sketch("//test:drawing") is not None


def test_the_exception_names_the_type_and_the_parameter():
    """What the message has to carry to be actionable."""
    error = ObjectTypeParameterException("sketch", "svg", "drawing", "include")
    assert "sketch type 'svg'" in str(error)
    assert "'include' parameter" in str(error)
    assert "drawing" in str(error)


def test_a_name_the_type_does_not_contribute_is_still_refused(tmp_path, caplog):
    """A typo must stay a typo rather than becoming a parameter nothing reads.

    Only the names the type contributes are declared on the object's behalf, so
    'includes' finds nothing to be and the reference is refused with the message
    it has always had.
    """
    ctx = _package(tmp_path, {"bends": {"type": "dxf"}})
    with caplog.at_level("ERROR"):
        assert ctx.get_sketch("//test:bends;includes=BEND_UP") is None
    assert "parametrize" in caplog.text

    # ...and the same on a sketch that does declare parameters, where it is the
    # setting of the value that refuses it and the message names it.
    ctx = _package(tmp_path, {"other": {"type": "dxf", "parameters": {"include": {"type": "array"}}}})
    with pytest.raises(ValueError, match="includes"):
        ctx.get_sketch("//test:other;includes=BEND_UP")


@pytest.mark.parametrize(
    "written,expected",
    [
        ("BEND_UP", ["BEND_UP"]),
        ("BEND_UP,BEND_DOWN", ["BEND_UP", "BEND_DOWN"]),
        ("BEND_UP, BEND_DOWN", ["BEND_UP", "BEND_DOWN"]),
        ("BEND_UP,", ["BEND_UP"]),
        ("", []),
    ],
)
def test_a_list_written_as_text_is_split_on_commas(tmp_path, written, expected):
    """A reference has only text to write with, so text is what arrives."""
    ctx = _package(tmp_path, {"bends": {"type": "dxf"}})
    reference = "//test:bends" + (";include=%s" % written if written else "")
    assert _layers(ctx.get_sketch(reference), "include") == expected


#
# The mechanism is not the sketch's alone
#


def test_a_part_type_parameter_needs_no_declaration_either(tmp_path):
    """The same rule, on the parameters a *part* type contributes.

    'Project.declare_object_type_parameters' is shared, so a homogeneous part
    that declares no 'parameters:' can still be asked for at a tolerance - which
    it could not be before, because it had nothing to apply the value to.
    Checked here because this is where that machinery is exercised.
    """
    (tmp_path / "partcad.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "//test",
                "parts": {"bracket": {"type": "stl", "manufacturing": {"method": "additive"}}},
            }
        )
    )
    (tmp_path / "bracket.stl").write_text("")
    ctx = pc.Context(str(tmp_path))

    part = ctx.get_part("//test:bracket;tolerance=0.2")
    assert part is not None
    assert part.get_object_type_parameter("tolerance") == pytest.approx(0.2)

    # ...and the part that was not asked keeps the default, and its cache key.
    plain = ctx.get_part("//test:bracket")
    assert plain.get_object_type_parameter("tolerance") == 0.0
    assert "parameters" not in plain.config


def test_a_part_type_that_rejects_the_parameter_still_rejects_it(tmp_path, caplog):
    """A 'step' file states its own material; declaring one is refused as before."""
    (tmp_path / "partcad.yaml").write_text(yaml.safe_dump({"name": "//test", "parts": {"bracket": {"type": "step"}}}))
    (tmp_path / "bracket.step").write_text("")
    ctx = pc.Context(str(tmp_path))

    with caplog.at_level("ERROR"):
        assert ctx.get_part("//test:bracket;material=steel") is None
    assert "parametrize" in caplog.text
