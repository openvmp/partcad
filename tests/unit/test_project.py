#!/usr/bin/env python3
#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.
#

import partcad as pc

test_config_import_git = {
    "name": "part_step",
    "type": "git",
    "url": "https://github.com/openvmp/partcad",
    "relPath": "examples/part_step",
}


def test_project_this_1():
    ctx = pc.Context("tests")
    prj = ctx.get_project("this")
    assert prj is not None


def test_project_this_2():
    ctx = pc.Context("examples/part_step")
    prj = ctx.get_project("this")
    assert prj is not None


def test_project_this_3():
    ctx = pc.Context("tests/partcad-examples.yaml")
    prj = ctx.get_project("this")
    assert prj is not None


def test_project_import_1():
    ctx = pc.Context()
    prj = ctx.import_project(test_config_import_git)
    assert prj is not None


def test_project_import_1():
    ctx = pc.Context()
    factory = pc.ProjectFactoryGit(ctx, test_config_import_git)
    assert factory.project is not None
