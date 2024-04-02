#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-20
#
# Licensed under Apache License, Version 2.0.

import sys
from types import ModuleType, FunctionType
from gc import get_referents

from . import consts

# Custom objects know their class.
# Function objects seem to know way too much, including modules.
# Exclude modules as well.
BLACKLIST = type, ModuleType, FunctionType


def get_child_project_path(parent_path, child_name):
    if parent_path.endswith("/"):
        return parent_path + child_name
    else:
        return parent_path + "/" + child_name


def resolve_resource_path(current_project_name, pattern: str):
    if ":" in pattern:
        project_pattern, item_pattern = pattern.split(":")
        if project_pattern == "":
            project_pattern = current_project_name
    else:
        project_pattern = pattern
        item_pattern = "*"

    project_pattern = project_pattern.replace("...", "*")
    item_pattern = item_pattern.replace("...", "*")

    return project_pattern, item_pattern


def normalize_resource_path(current_project_name, pattern: str):
    project_pattern, item_pattern = resolve_resource_path(
        current_project_name, pattern
    )
    return f"{project_pattern}:{item_pattern}"


def total_size(obj, verbose=False):
    """sum size of object & members."""
    if isinstance(obj, BLACKLIST):
        raise TypeError(
            "getsize() does not take argument of type: " + str(type(obj))
        )
    seen_ids = set()
    size = 0
    objects = [obj]
    while objects:
        need_referents = []
        for obj in objects:
            if not isinstance(obj, BLACKLIST) and id(obj) not in seen_ids:
                seen_ids.add(id(obj))
                s = sys.getsizeof(obj)
                if verbose:
                    print(s, type(obj), repr(obj), file=sys.stderr)
                size += s
                need_referents.append(obj)
        objects = get_referents(*need_referents)
    return size
