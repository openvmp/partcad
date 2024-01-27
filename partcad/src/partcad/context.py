#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.

import atexit
import importlib
import logging
import os

from . import consts
from . import project_config
from . import project
from . import runtime_python_all
from . import project_factory_local as rfl
from . import project_factory_git as rfg
from . import project_factory_tar as rft
from .user_config import user_config
from .utils import total_size


# Context
class Context(project_config.Configuration):
    """Stores and caches all imported objects."""

    stats_packages: int
    stats_packages_instantiated: int
    stats_parts: int
    stats_parts_instantiated: int
    stats_assemblies: int
    stats_assemblies_instantiated: int
    stats_memory: int

    def __init__(self, config_path="."):
        """Initializes the context and imports the root project."""
        super().__init__(consts.THIS, config_path)
        self.option_create_dirs = False
        self.runtimes_python = {}

        self.stats_packages = 0
        self.stats_packages_instantiated = 0
        self.stats_parts = 0
        self.stats_parts_instantiated = 0
        self.stats_assemblies = 0
        self.stats_assemblies_instantiated = 0
        self.stats_memory = 0

        if os.path.isdir(config_path):
            config_path = "."
        else:
            # TODO(clairbee): Add support for config files not at the top level
            config_path = os.path.basename(config_path)

        # self.projects contains all projects known to this context
        self.projects = {}
        self._projects_being_loaded = {}
        self._last_to_finalize = None

        spinner = None
        if logging.root.level < 60:
            try:
                progress = importlib.import_module("progress.spinner")
                if not progress is None:
                    spinner = progress.Spinner("PartCAD: Loading dependencies...")
                    spinner.start()
                    spinner.next()
            except Exception as e:
                print(e)
                _ignore = True

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

    def stats_recalc(self, verbose=False):
        self.stats_memory = total_size(self, verbose)

    def get_project(self, project_name) -> project.Project:
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

        self.stats_packages += 1
        self.stats_packages_instantiated += 1

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

    def get_part(self, part_name, project_name, params=None):
        prj = self.get_project(project_name)
        if prj is None:
            # Don't print anything as self.get_project is expected to report errors
            return None
        return prj.get_part(part_name, params)

    def get_assembly(self, assembly_name, project_name, params=None):
        prj = self.get_project(project_name)
        if prj is None:
            # Don't print anything as self.get_project is expected to report errors
            return None
        return prj.get_assembly(assembly_name, params)

    def finalize(self, shape, show_object_fn):
        self._last_to_finalize = shape
        self._show_object_fn = show_object_fn

    def _finalize_real(self):
        if self._last_to_finalize is not None:
            self._last_to_finalize._finalize_real(self._show_object_fn)
        self._last_to_finalize = None

    def render(self, format=None, output_dir=None):
        prj = self.get_project(consts.THIS)
        prj.render(format=format, output_dir=output_dir)

    def get_python_runtime(self, version, python_runtime=None):
        if python_runtime is None:
            python_runtime = user_config.python_runtime
        runtime_name = python_runtime + "-" + version
        if not runtime_name in self.runtimes_python:
            self.runtimes_python[runtime_name] = runtime_python_all.create(
                self, version, python_runtime
            )
        return self.runtimes_python[runtime_name]

    def ensure_dirs(self, path):
        if not self.option_create_dirs:
            return
        os.makedirs(path)

    def ensure_dirs_for_file(self, filename):
        if not self.option_create_dirs:
            return
        path = os.path.dirname(filename)
        os.makedirs(path)
