#!/usr/bin/env python3
#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-27
#
# Licensed under Apache License, Version 2.0.
#

import partcad as pc


def test_project_config_version_1():
    """Positive test case for PartCAD version requirement in the package config file"""
    try:
        ctx = pc.Context("tests/unit/data/project_config_valid_1.yaml")
        assert ctx.config_obj["partcad"] == ">=0.1.0"
    except Exception as e:
        assert False, "Valid configuration file caused an exception: %s" % e


def test_project_config_version_2():
    """Negative test case for PartCAD version requirement in the package config file"""
    try:
        ctx = pc.Context("tests/unit/data/project_config_invalid_1.yaml")
        assert False, "Invalid configuration file did not cause an exception"
    except:
        _ignore = True