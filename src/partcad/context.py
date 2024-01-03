#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.

import atexit
import logging
import os
from progress.spinner import Spinner

from . import consts
from . import project_config
from . import runtime_python_all
from . import project_factory_local as rfl
from . import project_factory_git as rfg
from . import project_factory_tar as rft
from .user_config import user_config

global _partcad_context
_partcad_context = None


def init(config_path="."):
    """Initialize the default context explicitly using the desired path."""
    global _partcad_context
    global _partcad_context_path

    if _partcad_context is None:
        # logging.debug("Initializing (%s)..." % __name__)

        _partcad_context = Context(config_path)
        _partcad_context_path = config_path
    else:
        if _partcad_context_path != config_path:
            logging.error("Multiple context configurations")
            raise Exception("partcad: multiple context configurations")

    return _partcad_context


def get_assembly(assembly_name, project_name=consts.THIS):
    """Get the assembly from the given project"""
    if project_name is None:
        project_name = consts.THIS
    return init().get_assembly(assembly_name, project_name)


def get_part(part_name, project_name=consts.THIS):
    """Get the part from the given project"""
    if project_name is None:
        project_name = consts.THIS
    return init().get_part(part_name, project_name)


def finalize(shape, show_object_fn):
    return init().finalize(shape, show_object_fn)


def finalize_real():
    return init()._finalize_real(True)


def render():
    return init().render()


# Context
class Context(project_config.Configuration):
    """Stores and caches all imported objects."""

    def __init__(self, config_path="."):
        """Initializes the context and imports the root project."""
        super().__init__(config_path)
        self.runtimes_python = {}

        if os.path.isdir(config_path):
            config_path = "."
        else:
            # TODO(clairbee): Add support for config files not at the top level
            config_path = os.path.basename(config_path)

        # self.projects contains all projects known to this context
        self.projects = {}
        self._projects_being_loaded = {}
        self._last_to_finalize = None

        if logging.root.level < 60:
            spinner = Spinner("PartCAD: Loading dependencies...")
            spinner.start()
            spinner.next()
        else:
            spinner = None

        self.import_project(
            None,  # parent
            {
                "name": consts.THIS,
                "type": "local",
                "path": config_path,
            },
            spinner=spinner,
        )
        if not spinner is None:
            spinner.finish()
            logging.info("PartCAD: Finished loading dependencies.")

        atexit.register(Context._finalize_real, self)

    def get_project(self, project_name):
        if not project_name in self.projects:
            logging.error("The project '%s' is not found." % project_name)
            logging.error("%s" % self.projects)
            return None

        config = self.projects[project_name]
        return config

    def import_project(self, parent, project_import_config, spinner=None):
        if not "name" in project_import_config or not "type" in project_import_config:
            logging.error(
                "Invalid project configuration found: %s" % project_import_config
            )
            return None

        name = project_import_config["name"]

        if not spinner is None:
            spinner.message = "PartCAD: Loading %s..." % name
            spinner.next()

        if name in self._projects_being_loaded:
            logging.error("Recursive project loading detected (%s), aborting." % name)
            return None

        # Depending on the project type, use different factories
        if (
            not "type" in project_import_config
            or project_import_config["type"] == "local"
        ):
            rfl.ProjectFactoryLocal(self, parent, project_import_config)
        elif project_import_config["type"] == "git":
            rfg.ProjectFactoryGit(self, parent, project_import_config)
        elif project_import_config["type"] == "tar":
            rft.ProjectFactoryTar(self, parent, project_import_config)
        else:
            logging.error("Invalid project type found: %s." % name)
            return None

        if not spinner is None:
            spinner.next()

        # Check whether the factory was able to successfully add the project
        if not name in self.projects:
            logging.error("Failed to create the project: %s" % project_import_config)
            return None

        imported_project = self.projects[name]

        # Load the dependencies recursively
        # while preventing circular dependencies
        self._projects_being_loaded[name] = True
        # logging.debug("Imported config: %s..." % imported_project.config_obj)
        if "import" in imported_project.config_obj:
            for prj_name in imported_project.config_obj["import"]:
                # logging.debug("Importing: %s..." % prj_name)
                prj_conf = imported_project.config_obj["import"][prj_name]
                prj_conf["name"] = prj_name
                self.import_project(imported_project, prj_conf, spinner=spinner)
        del self._projects_being_loaded[name]

        if not spinner is None:
            spinner.next()

        return imported_project

    def get_part(self, part_name, project_name):
        prj = self.get_project(project_name)
        if prj is None:
            # Don't print anything as self.get_project is expected to report errors
            return None
        return prj.get_part(part_name)

    def get_assembly(self, assembly_name, project_name):
        prj = self.get_project(project_name)
        if prj is None:
            # Don't print anything as self.get_project is expected to report errors
            return None
        return prj.get_assembly(assembly_name)

    def finalize(self, shape, show_object_fn):
        self._last_to_finalize = shape
        self._show_object_fn = show_object_fn

    def _finalize_real(self, embedded=False):
        """
        embedded: PartCAD within PartCAD. True if
          - this is a PartCAD module (calls pc.finalize() at the end, not show_object())
            - internally pc.finalize() uses atexit() to schedule show_object()
          - it is being called by PartCAD using CQGI
            - atexit() handlers are not getting called until the process exits
        """
        if self._last_to_finalize is not None:
            self._last_to_finalize._finalize_real(
                self._show_object_fn, embedded=embedded
            )
        self._last_to_finalize = None

    def render(self):
        prj = self.get_project(consts.THIS)
        prj.render()

    def get_python_runtime(self, version, python_runtime=None):
        if python_runtime is None:
            python_runtime = user_config.python_runtime
        runtime_name = python_runtime + "-" + version
        if not runtime_name in self.runtimes_python:
            self.runtimes_python[runtime_name] = runtime_python_all.create(
                self, version, python_runtime
            )
        return self.runtimes_python[runtime_name]
