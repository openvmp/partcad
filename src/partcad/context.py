#!/usr/bin/env python3
#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.

import os
import atexit

from . import project_config
from . import project_factory_local as rfl
from . import project_factory_git as rfg

global _partcad_context
_partcad_context = None


def init(config_path="."):
    """Initialize the default context explicitly using the desired path."""
    global _partcad_context
    global _partcad_context_path

    if _partcad_context is None:
        print("Initializing (%s)..." % __name__)

        _partcad_context = Context(config_path)
        _partcad_context_path = config_path
    else:
        if _partcad_context_path != config_path:
            print("Error: multiple context configurations")
            raise Exception("partcad: multiple context configurations")

    return _partcad_context


def get_part(project_name, part_name):
    """Get the part for a given project"""
    return init().get_part(project_name, part_name)


def finalize(shape):
    return init().finalize(shape)


# Context
class Context(project_config.Configuration):
    """Stores and caches all imported objects."""

    def __init__(self, config_path="."):
        """Initializes the context and imports the root project."""
        super().__init__(config_path)

        if os.path.isdir(config_path):
            config_path = "."
        else:
            # TODO(clairbee): Add support for config files not at the top level
            config_path = os.path.basename(config_path)

        # self.projects contains all projects known to this context
        self.projects = {}
        self._projects_being_loaded = {}
        self._last_to_finalize = None

        self.import_project(
            None,  # parent
            {
                "name": "this",
                "type": "local",
                "path": config_path,
            },
        )

        atexit.register(Context._finalize_real, self)

    def get_project(self, project_name):
        if not project_name in self.projects:
            print("The project '%s' is not found." % project_name)
            print("%s" % self.projects)
            return None

        config = self.projects[project_name]
        return config

    def import_project(self, parent, project_import_config):
        if not "name" in project_import_config or not "type" in project_import_config:
            print("Invalid project configuration found: %s" % project_import_config)
            return None

        name = project_import_config["name"]

        print("Importing project: %s..." % name)

        if name in self._projects_being_loaded:
            print("Recursive project loading detected (%s), aborting." % name)
            return None

        # Depending on the project type, use different factories
        if (
            not "type" in project_import_config
            or project_import_config["type"] == "local"
        ):
            rfl.ProjectFactoryLocal(self, parent, project_import_config)
        elif project_import_config["type"] == "git":
            rfg.ProjectFactoryGit(self, parent, project_import_config)
        else:
            print("Invalid project type found: %s." % name)
            return None

        # Check whether the factory was able to successfully add the project
        if not name in self.projects:
            print("Failed to create the project: %s" % project_import_config)
            return None

        imported_project = self.projects[name]

        # Load the dependencies recursively
        # while preventing circular dependencies
        self._projects_being_loaded[name] = True
        print("Imported config: %s..." % imported_project.config_obj)
        if "import" in imported_project.config_obj:
            for prj_name in imported_project.config_obj["import"]:
                prj_conf = imported_project.config_obj["import"][prj_name]
                prj_conf["name"] = prj_name
                self.import_project(imported_project, prj_conf)
        del self._projects_being_loaded[name]

        return imported_project

    def get_part(self, project_name, part_name):
        prj = self.get_project(project_name)
        if prj is None:
            # Don't print anything as self.get_project is expected to report errors
            return None
        return prj.get_part(part_name)

    def get_assembly(self, project_name, assembly_name):
        prj = self.get_project(project_name)
        if prj is None:
            # Don't print anything as self.get_project is expected to report errors
            return None
        return prj.get_assembly(assembly_name)

    def finalize(self, shape):
        self._last_to_finalize = shape

    def _finalize_real(self):
        if self._last_to_finalize is not None:
            self._last_to_finalize._finalize_real()
        self._last_to_finalize = None
