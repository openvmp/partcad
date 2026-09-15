#
# PartCAD, 2026
#
# Licensed under Apache License, Version 2.0.
#
"""Unit tests for the `cam:` section: how a route picks its implementation.

`cam:` is an output section of the same shape as `export:` and `render:` and is
resolved by the same code, which is the point of it - and also the risk. What is
checked here is that it stays its own section and resolves the way it says it
does:

* a `cam:` file type is **not** an output format. `pc render -t gcode` must not
  find it, and it must not fall back to a render implementation.
* unlike `cae:`, it has a built-in package, and the shipped default names it.
* the implementation comes from the user configuration by default, is named as
  `<package>:<file type>`, and the file it writes is named after the object
  alone - `panel.nc`, because an object has one route at a time.

No machine and no sandbox: everything here stops at the point where the script
would be run.
"""

import asyncio
import os
import textwrap

import pytest

import partcad as pc
from partcad import cam, output

EXAMPLES = "examples"


@pytest.fixture(scope="module")
def ctx():
    """A context over the shipped examples, for the questions about `//builtin`."""
    return pc.Context(EXAMPLES)


# --------------------------------------------------------------------------- #
# The section is its own                                                      #
# --------------------------------------------------------------------------- #


def test_cam_is_not_an_output_section():
    """'pc export'/'pc render' must not offer a route as a file type."""
    assert output.CAM not in output.SECTIONS
    assert output.CAM in output.ALL_SECTIONS


def test_cam_is_not_an_analysis_either():
    """A route makes the object; an analysis reports on one. Nothing may confuse them."""
    assert output.CAM not in output.ANALYSIS_SECTIONS
    assert output.CAE not in output.MANUFACTURING_SECTIONS


def test_cam_has_no_fallback_section():
    """A render implementation cannot stand in for a post-processor, or the reverse."""
    assert output.config_sections(output.CAM) == (output.CAM,)
    assert output.CAM not in output.config_sections(output.EXPORT)
    assert output.CAM not in output.config_sections(output.RENDER)


def test_a_route_is_not_a_known_output_format(ctx):
    """'gcode' is not something 'pc render -t' or 'pc export -t' can name."""
    assert output.section_of(ctx, "gcode") is None
    assert "gcode" not in output.all_formats(ctx)


# --------------------------------------------------------------------------- #
# Unlike an analysis, PartCAD ships one                                       #
# --------------------------------------------------------------------------- #


def test_cam_has_a_builtin_package(ctx):
    """A route is arithmetic on the object's own outline, so it ships here.

    This is the one place `cam:` and `cae:` genuinely differ, and it is what
    makes `pc cam` work in a package that says nothing about machines.
    """
    assert output.BUILTIN_PACKAGES[output.CAM] == "//builtin/cam"
    assert output.builtin_project(ctx, output.CAM) is not None
    assert "gcode" in output.builtin_formats(ctx, output.CAM)


def test_the_builtin_route_declares_what_it_writes(ctx):
    """An implementation that does not say is a bug in that package.

    There is no default extension for a route to fall back on -- what a
    controller reads is the implementation's decision -- so the shipped one has
    to state it.
    """
    gcode = output.builtin_formats(ctx, output.CAM)["gcode"]
    assert gcode["extension"] == "nc"
    assert gcode["path"] == "cam_gcode.py"


def test_the_builtin_route_declares_no_tool(ctx):
    """The one parameter that cannot be guessed from the part is not defaulted.

    Every other parameter has a defensible default; a route produced against a
    cutter diameter nobody chose is wrong by exactly the amount nobody noticed.
    """
    assert "tool" not in output.builtin_formats(ctx, output.CAM)["gcode"]


def test_the_default_implementation_is_the_builtin_one(ctx):
    assert ctx.user_config.cam_implementation == "//builtin/cam:gcode"


# --------------------------------------------------------------------------- #
# Resolving an implementation                                                 #
# --------------------------------------------------------------------------- #

PACKAGE = textwrap.dedent("""
    name: //cam-test
    parts:
      panel:
        type: step
        path: panel.step
        cam:
          tool: 6 mm
          depth: 18 mm
      lid:
        type: step
        path: panel.step
        cam:
          tool: 3 mm
          implementation: //cam-test:router
      plain:
        type: step
        path: panel.step
      broken:
        type: step
        path: panel.step
        cam:
          tool: six millimetres
    cam:
      gcode:
        feed: 2400
        depth_per_pass: 3
      router:
        path: route.py
        extension: tap
        feed: 900
      nothing:
        # Declared without an 'extension:', which a route has no default for: a
        # misconfigured plugin, as opposed to a missing one.
        path: route.py
    """)


@pytest.fixture
def package(tmp_path):
    """A package that declares a route implementation of its own."""
    (tmp_path / "partcad.yaml").write_text(PACKAGE)
    (tmp_path / "route.py").write_text("def process(path, request):\n    return {'success': True}\n")
    # Not read by anything here: a part is resolved from its declaration, and
    # the geometry is only built when something asks for it.
    (tmp_path / "panel.step").write_text("")
    return pc.Context(str(tmp_path))


def _part(package, name):
    part = package.get_part(":" + name)
    assert part is not None
    return part


def test_a_route_is_named_after_the_object_alone(package):
    """'panel.nc', not 'panel.cam.nc': an object has one route at a time.

    The extension already says what the file is, which is what separates this
    from an analysis -- a part has as many results as it has analyses, so those
    carry the analysis in the name.
    """
    part = _part(package, "panel")
    impl, filepath = part.cam_getopts(package, "gcode", package.get_project("//cam-test"))
    assert os.path.basename(filepath) == "panel.nc"
    assert impl.section == output.CAM


def test_the_package_layer_re_tunes_the_builtin_one(package):
    """What a package sets under its own `cam:` covers every object in it.

    The built-in package is the bottom layer, so a package that changes one
    parameter keeps the built-in implementation for everything else -- which is
    the whole reason a route is configured as an output file type.
    """
    part = _part(package, "panel")
    impl, _ = part.cam_getopts(package, "gcode", package.get_project("//cam-test"))
    assert impl.parameters["feed"] == 2400
    assert impl.parameters["safe_z"] == 5
    assert impl.script == "cam_gcode.py"


def test_an_implementation_that_does_not_say_what_it_writes_is_refused(package):
    part = _part(package, "panel")
    with pytest.raises(Exception) as raised:
        part.cam_getopts(package, "nothing", package.get_project("//cam-test"))
    assert "extension" in str(raised.value)


def test_the_object_outranks_the_user_configuration(package):
    """An object naming an implementation is saying which machine it was written for."""
    part = _part(package, "lid")
    config = cam.config_of(part)
    assert config.implementation == "//cam-test:router"
    options_project, format_name = part._route_implementation(package, None, declared=config.implementation)
    assert (options_project.name, format_name) == ("//cam-test", "router")


def test_the_command_line_outranks_the_object(package):
    """'-i' is the most specific thing anybody said, so it wins."""
    part = _part(package, "lid")
    options_project, format_name = part._route_implementation(package, "//cam-test:gcode", declared="//cam-test:router")
    assert (options_project.name, format_name) == ("//cam-test", "gcode")


def test_a_package_on_its_own_means_its_gcode(package):
    """What a package publishing one route implementation is most likely to call it."""
    part = _part(package, "panel")
    options_project, format_name = part._route_implementation(package, "//cam-test")
    assert (options_project.name, format_name) == ("//cam-test", "gcode")


def test_an_implementation_in_a_package_that_is_not_there_says_so(package):
    part = _part(package, "panel")
    with pytest.raises(Exception) as raised:
        part._route_implementation(package, "//nowhere:gcode")
    assert "is not found" in str(raised.value)


# --------------------------------------------------------------------------- #
# Which objects a package-level run visits                                    #
# --------------------------------------------------------------------------- #


def test_a_package_run_visits_the_objects_that_declare_a_section(package):
    """The `cam:` section is the opt-in, and the whole of it.

    `broken` is in the list although its section cannot be read: deciding what
    to visit must not raise on one object's mistake, or a package where one
    part has a typo produces no routes at all instead of nineteen and a report.
    That is why `cam.declared_config()` exists beside `config_of()`.
    """
    project = package.get_project("//cam-test")
    routable = asyncio.run(project.routable_shapes_async())
    assert sorted(shape.name for shape in routable) == ["broken", "lid", "panel"]


def test_an_object_asked_for_by_name_is_visited_whatever_it_declares(package):
    """The refusal belongs to `route_async()`, which says which object and which section.

    Naming an object is asking about that object; coming back with nothing would
    make `pc cam :plain` look exactly like a route that went somewhere the user
    did not notice.
    """
    project = package.get_project("//cam-test")
    routable = asyncio.run(project.routable_shapes_async(parts=["plain"]))
    assert [shape.name for shape in routable] == ["plain"]


def test_a_broken_section_is_reported_against_the_object_it_is_on(package):
    """A run over a package prints one line per object, so each needs an address.

    "'cam: tool:' is not a length" against forty parts is a sentence with no
    address on it. `partcad.cam` deliberately knows nothing about shapes, so the
    naming happens where the object is known -- once, on the way out of
    `route_async()`.
    """
    part = _part(package, "broken")
    with pytest.raises(cam.CamConfigError) as raised:
        asyncio.run(part.route_async(package))
    message = str(raised.value)
    assert message.startswith("//cam-test:broken: ")
    assert "is not a length" in message


def test_an_object_with_no_section_says_so_by_name(package):
    """Naming an object is asking about it, so "nothing to route" names it back."""
    part = _part(package, "plain")
    with pytest.raises(cam.CamConfigError) as raised:
        asyncio.run(part.route_async(package))
    assert "//cam-test:plain declares no 'cam:' section" in str(raised.value)
