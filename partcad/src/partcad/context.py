#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.

import asyncio
import os
import threading

from . import consts
from . import logging as pc_logging
from .mating import Mating
from . import project_config
from . import runtime_python_all
from . import project_factory_local as rfl
from . import project_factory_git as rfg
from . import project_factory_tar as rft
from .user_config import user_config
from .utils import *


# Context
class Context(project_config.Configuration):
    """Stores and caches all imported objects."""

    stats_packages: int
    stats_packages_instantiated: int
    stats_sketches: int
    stats_sketches_instantiated: int
    stats_interfaces: int
    stats_interfaces_instantiated: int
    stats_parts: int
    stats_parts_instantiated: int
    stats_assemblies: int
    stats_assemblies_instantiated: int
    stats_memory: int

    def __init__(self, root_path=None, search_root=True):
        """Initializes the context and imports the root project."""
        root_file = ""
        if root_path is None:
            # Find the top folder containing "partcad.yaml"
            root_path = "."
        else:
            if os.path.isfile(root_path):
                root_file = os.path.basename(root_path)
                root_path = os.path.dirname(root_path)
        initial_root_path = os.path.abspath(root_path)
        if search_root:
            while os.path.exists(os.path.join(root_path, "..", "partcad.yaml")):
                root_path = os.path.join(root_path, "..")
        self.root_path = os.path.abspath(root_path)
        if self.root_path == initial_root_path and root_file != "":
            self.root_path = os.path.join(self.root_path, root_file)
        self.current_project_path = "/" + os.path.relpath(
            initial_root_path,
            root_path,
        )
        if self.current_project_path == "/.":
            self.current_project_path = "/"
        super().__init__(consts.ROOT, self.root_path)

        # Protect the critical sections from access in different threads
        self.lock = threading.RLock()

        self.option_create_dirs = False
        self.runtimes_python = {}

        self.stats_packages = 0
        self.stats_packages_instantiated = 0
        self.stats_interfaces = 0
        self.stats_interfaces_instantiated = 0
        self.stats_sketches = 0
        self.stats_sketches_instantiated = 0
        self.stats_parts = 0
        self.stats_parts_instantiated = 0
        self.stats_assemblies = 0
        self.stats_assemblies_instantiated = 0
        self.stats_memory = 0

        self.mates = {}
        # self.projects contains all projects known to this context
        self.projects = {}
        self._projects_being_loaded = {}

        with pc_logging.Process("InitCtx", self.config_dir):
            self.import_project(
                None,  # parent
                {
                    "name": consts.ROOT,
                    "type": "local",
                    "path": self.config_path,
                    "maybeEmpty": True,
                },
            )

    def stats_recalc(self, verbose=False):
        self.stats_memory = total_size(self, verbose)

    def get_current_project_path(self):
        return self.current_project_path

    def import_project(self, parent, project_import_config):
        if (
            not "name" in project_import_config
            or not "type" in project_import_config
        ):
            pc_logging.error(
                "Invalid project configuration found: %s"
                % project_import_config
            )
            return None

        name = project_import_config["name"]
        with pc_logging.Action("Import", name):
            if name in self._projects_being_loaded:
                pc_logging.error(
                    "Recursive project loading detected (%s), aborting." % name
                )
                return None
            self._projects_being_loaded[name] = True

            # Depending on the project type, use different factories
            if (
                not "type" in project_import_config
                or project_import_config["type"] == "local"
            ):
                rfl.ProjectFactoryLocal(self, parent, project_import_config)
            elif project_import_config["type"] == "git":
                with pc_logging.Action("Git", name):
                    rfg.ProjectFactoryGit(self, parent, project_import_config)
            elif project_import_config["type"] == "tar":
                with pc_logging.Action("Tar", name):
                    rft.ProjectFactoryTar(self, parent, project_import_config)
            else:
                pc_logging.error("Invalid project type found: %s." % name)
                del self._projects_being_loaded[name]
                return None

            # Check whether the factory was able to successfully add the project
            if not name in self.projects:
                pc_logging.error(
                    "Failed to create the project: %s" % project_import_config
                )
                del self._projects_being_loaded[name]
                return None

            imported_project = self.projects[name]
            if imported_project is None:
                pc_logging.error("Failed to import the package: %s" % name)
                del self._projects_being_loaded[name]
                return None
            if imported_project.broken:
                pc_logging.error(
                    "Failed to parse the package's 'partcad.yaml': %s" % name
                )

            self.stats_packages += 1
            self.stats_packages_instantiated += 1

            del self._projects_being_loaded[name]
            return imported_project

    def get_project_abs_path(self, rel_project_path: str):
        if rel_project_path.startswith("/"):
            return rel_project_path

        project_path = self.current_project_path

        if rel_project_path == ".":
            rel_project_path = ""
        if rel_project_path == "":
            return project_path

        if not project_path.endswith("/"):
            project_path += "/"
        return os.path.abspath(project_path + rel_project_path)

    def get_project(self, rel_project_path: str):
        project_path = self.get_project_abs_path(rel_project_path)

        with self.lock:
            # Strip the first '/' (absolute path always starts with a '/'``)
            project_path = project_path[1:]

            project = self.projects[consts.ROOT]

            if project_path == "":
                return project
            else:
                import_list = project_path.split("/")

            return self._get_project_recursive(project, import_list)

    def _get_project_recursive(self, project, import_list: list[str]):
        """Load the dependencies recursively"""
        if len(import_list) == 0:
            # Found what we are looking for
            return project

        # next_import is the next of the import we need to load now
        next_import = import_list[0]
        # import_list is reduced to contain only the items that will remain to
        # bt loaded after this import
        import_list = import_list[1:]

        # next_project will reference the project we are importing now
        next_project = None
        # next_project_path is the full path of the project we are importing now
        next_project_path = get_child_project_path(project.name, next_import)

        # see if the wanted project is already initialized
        if next_project_path in self.projects:
            return self._get_project_recursive(
                self.projects[next_project_path], import_list
            )

        # Check if there is a matching subfolder
        subfolders = [
            f.name for f in os.scandir(project.config_dir) if f.is_dir()
        ]
        if next_import in list(subfolders):
            if os.path.exists(
                os.path.join(
                    project.config_dir,
                    next_import,
                    consts.DEFAULT_PACKAGE_CONFIG,
                )
            ):
                pc_logging.debug(
                    "Importing a subfolder: %s..." % next_project_path
                )
                prj_conf = {
                    "name": next_project_path,
                    "type": "local",
                    "path": next_import,
                }
                next_project = self.import_project(project, prj_conf)
                if not next_project is None:
                    result = self._get_project_recursive(
                        next_project, import_list
                    )
                    return result
        else:
            # Otherwise, iterate all subfolders and check if any of them are packages
            if (
                "import" in project.config_obj
                and not project.config_obj["import"] is None
            ):
                imports = project.config_obj["import"]
                if project.path != self.root_path:
                    filtered = filter(
                        lambda x: "onlyInRoot" not in imports[x]
                        or not imports[x]["onlyInRoot"],
                        imports,
                    )
                    imports = list(filtered)
                for prj_name in imports:
                    pc_logging.debug("Checking the import: %s..." % prj_name)
                    if prj_name != next_import:
                        continue
                    pc_logging.debug("Importing: %s..." % next_project_path)
                    prj_conf = project.config_obj["import"][prj_name]
                    if "name" in prj_conf:
                        prj_conf["orig_name"] = prj_conf["name"]
                    prj_conf["name"] = next_project_path
                    next_project = self.import_project(project, prj_conf)
                    if not next_project is None:
                        result = self._get_project_recursive(
                            next_project, import_list
                        )
                        return result
                    break

        return next_project

    def import_all(self):
        self._import_all_recursive(self.projects[consts.ROOT])

    def _import_all_recursive(self, project):
        if project.broken:
            pc_logging.info("Ignoring the broken package: %s" % project.name)
            return

        # First, iterate all explicitly mentioned "import"s.
        # Do it before iterating subdirectories, as it may kick off a long
        # background task.
        if (
            "import" in project.config_obj
            and not project.config_obj["import"] is None
        ):
            imports = project.config_obj["import"]
            if project.path != self.root_path:
                filtered = filter(
                    lambda x: "onlyInRoot" not in imports[x]
                    or not imports[x]["onlyInRoot"],
                    imports,
                )
                imports = list(filtered)
            for prj_name in imports:
                next_project_path = get_child_project_path(
                    project.name, prj_name
                )

                pc_logging.debug("Importing: %s..." % next_project_path)
                prj_conf = project.config_obj["import"][prj_name]
                if "name" in prj_conf:
                    prj_conf["orig_name"] = prj_conf["name"]
                prj_conf["name"] = next_project_path
                next_project = self.import_project(project, prj_conf)
                self._import_all_recursive(next_project)

        # Second, iterate over all subfolder and check for packages
        subfolders = [
            f.name for f in os.scandir(project.config_dir) if f.is_dir()
        ]
        for subdir in list(subfolders):
            if os.path.exists(
                os.path.join(
                    project.config_dir,
                    subdir,
                    consts.DEFAULT_PACKAGE_CONFIG,
                )
            ):
                next_project_path = get_child_project_path(project.name, subdir)
                pc_logging.debug(
                    "Importing a subfolder: %s..." % next_project_path
                )
                prj_conf = {
                    "name": next_project_path,
                    "type": "local",
                    "path": subdir,
                }
                next_project = self.import_project(project, prj_conf)
                self._import_all_recursive(next_project)

    def get_all_packages(self):
        # TODO(clairbee): leverage root_project.get_child_project_names()
        self.import_all()
        return self.get_packages()

    def get_packages(self):
        return map(
            lambda pkg: {"name": pkg.name, "desc": pkg.desc},
            filter(
                lambda x: len(x.sketches) + len(x.parts) + len(x.assemblies)
                > 0,
                self.projects.values(),
            ),
        )

    def add_mate(
        self, source_interface, target_interface, mate_target_config: dict
    ):
        self._add_mate(
            source_interface,
            target_interface,
            mate_target_config,
            reverse=False,
        )
        self._add_mate(
            target_interface,
            source_interface,
            mate_target_config,
            reverse=True,
        )

    def _add_mate(
        self,
        source_interface,
        target_interface,
        mate_target_config: dict,
        reverse: bool,
    ):
        source_interface_name = source_interface.full_name
        target_interface_name = target_interface.full_name

        if not source_interface_name in self.mates:
            self.mates[source_interface_name] = {}
        if target_interface_name in self.mates[source_interface_name]:
            raise Exception(
                "Mate already exists: %s -> %s"
                % (source_interface_name, target_interface_name)
            )

        mate = Mating(
            source_interface, target_interface, mate_target_config, reverse
        )
        self.mates[source_interface_name][target_interface_name] = mate

    def get_mate(self, source_interface_name, target_interface_name):
        if not source_interface_name in self.mates:
            return None
        if not target_interface_name in self.mates[source_interface_name]:
            return None

        return self.mates[source_interface_name][target_interface_name]

    def find_mating_interfaces(self, source_shape, target_shape):
        source_interfaces = set(source_shape.with_ports.get_interfaces().keys())
        compatible_source_interfaces = set(
            [
                compatible_interface
                for interface in source_interfaces
                for compatible_interface in self.get_interface(
                    interface
                ).compatible_with
            ]
        )
        real_source_interfaces = {
            interface: set([interface]) for interface in source_interfaces
        }
        for interface in source_interfaces:
            for compatible_interface in self.get_interface(
                interface
            ).compatible_with:
                if not compatible_interface in real_source_interfaces:
                    real_source_interfaces[compatible_interface] = set()
                real_source_interfaces[compatible_interface].add(interface)
        source_interfaces = source_interfaces.union(
            compatible_source_interfaces
        )
        pc_logging.debug("Source interfaces: %s" % source_interfaces)

        target_interfaces = set(target_shape.with_ports.get_interfaces().keys())
        compatible_target_interfaces = set(
            [
                compatible_interface
                for interface in target_interfaces
                for compatible_interface in self.get_interface(
                    interface
                ).compatible_with
            ]
        )
        real_target_interfaces = {
            interface: set([interface]) for interface in target_interfaces
        }
        for interface in target_interfaces:
            for compatible_interface in self.get_interface(
                interface
            ).compatible_with:
                if not compatible_interface in real_target_interfaces:
                    real_target_interfaces[compatible_interface] = set()
                real_target_interfaces[compatible_interface].add(interface)
        target_interfaces = target_interfaces.union(
            compatible_target_interfaces
        )
        pc_logging.debug("Target interfaces: %s" % target_interfaces)

        source_interfaces_mates = set(
            [
                peer_interface
                for source_interface in source_interfaces
                for peer_interface in self.mates.get(
                    source_interface, {}
                ).keys()
            ]
        )
        target_interfaces_mates = set(
            [
                peer_interface
                for target_interface in target_interfaces
                for peer_interface in self.mates.get(
                    target_interface, {}
                ).keys()
            ]
        )
        source_candidate_interfaces = source_interfaces.intersection(
            target_interfaces_mates
        )
        real_source_candidate_interfaces = set()
        for source_interface in source_candidate_interfaces:
            real_source_candidate_interfaces = (
                real_source_candidate_interfaces.union(
                    real_source_interfaces[source_interface]
                )
            )
        source_candidate_interfaces = real_source_candidate_interfaces
        pc_logging.debug(
            "Source candidate interfaces: %s" % source_candidate_interfaces
        )

        target_candidate_interfaces = target_interfaces.intersection(
            source_interfaces_mates
        )
        real_target_candidate_interfaces = set()
        for target_interface in target_candidate_interfaces:
            real_target_candidate_interfaces = (
                real_target_candidate_interfaces.union(
                    real_target_interfaces[target_interface]
                )
            )
        target_candidate_interfaces = real_target_candidate_interfaces
        pc_logging.debug(
            "Target candidate interfaces: %s" % target_candidate_interfaces
        )

        return source_candidate_interfaces, target_candidate_interfaces

    def _get_sketch(self, sketch_spec, params=None):
        project_name, sketch_name = resolve_resource_path(
            self.current_project_path,
            sketch_spec,
        )
        prj = self.get_project(project_name)
        if prj is None:
            pc_logging.error("Package %s not found" % project_name)
            pc_logging.error("Packages found: %s" % str(self.projects))
            return None
        pc_logging.debug("Retrieving %s from %s" % (sketch_name, project_name))
        return prj.get_sketch(sketch_name, params)

    def get_sketch(self, sketch_spec, params=None):
        return self._get_sketch(sketch_spec, params)

    def get_sketch_shape(self, sketch_spec, params=None):
        return asyncio.run(self._get_sketch(sketch_spec, params).get_wrapped())

    def get_sketch_cadquery(self, sketch_spec, params=None):
        return asyncio.run(self._get_sketch(sketch_spec, params).get_cadquery())

    def get_sketch_build123d(self, sketch_spec, params=None):
        return asyncio.run(
            self._get_sketch(sketch_spec, params).get_build123d()
        )

    def _get_interface(self, interface_spec):
        project_name, interface_name = resolve_resource_path(
            self.current_project_path,
            interface_spec,
        )
        prj = self.get_project(project_name)
        if prj is None:
            pc_logging.error("Package %s not found" % project_name)
            pc_logging.error("Packages found: %s" % str(self.projects))
            return None
        pc_logging.debug(
            "Retrieving %s from %s" % (interface_name, project_name)
        )
        return prj.get_interface(interface_name)

    def get_interface(self, interface_spec):
        return self._get_interface(interface_spec)

    def get_interface_shape(self, interface_spec):
        return asyncio.run(self._get_interface(interface_spec).get_wrapped())

    def _get_part(self, part_spec, params=None):
        project_name, part_name = resolve_resource_path(
            self.current_project_path,
            part_spec,
        )
        prj = self.get_project(project_name)
        if prj is None:
            pc_logging.error("Package %s not found" % project_name)
            pc_logging.error("Packages found: %s" % str(self.projects))
            return None
        pc_logging.debug("Retrieving %s from %s" % (part_name, project_name))
        return prj.get_part(part_name, params)

    def get_part(self, part_spec, params=None):
        return self._get_part(part_spec, params)

    def get_part_shape(self, part_spec, params=None):
        return asyncio.run(self._get_part(part_spec, params).get_wrapped())

    def get_part_cadquery(self, part_spec, params=None):
        return asyncio.run(self._get_part(part_spec, params).get_cadquery())

    def get_part_build123d(self, part_spec, params=None):
        return asyncio.run(self._get_part(part_spec, params).get_build123d())

    def _get_assembly(self, assembly_spec, params=None):
        project_name, assembly_name = resolve_resource_path(
            self.current_project_path,
            assembly_spec,
        )
        prj = self.get_project(project_name)
        if prj is None:
            pc_logging.error("Package %s not found" % project_name)
            return None
        pc_logging.debug(
            "Retrieving %s from %s" % (assembly_name, project_name)
        )
        return prj.get_assembly(assembly_name, params)

    def get_assembly(self, assembly_spec, params=None):
        return self._get_assembly(assembly_spec, params)

    def get_assembly_shape(self, assembly_spec, params=None):
        return asyncio.run(
            self._get_assembly(assembly_spec, params).get_wrapped()
        )

    def get_assembly_cadquery(self, assembly_spec, params=None):
        return asyncio.run(
            self._get_assembly(assembly_spec, params).get_cadquery()
        )

    def get_assembly_build123d(self, assembly_spec, params=None):
        return asyncio.run(
            self._get_assembly(assembly_spec, params).get_build123d()
        )

    def render(self, project_path=None, format=None, output_dir=None):
        if project_path is None:
            project_path = self.get_current_project_path()
        pc_logging.info("Rendering all objects in %s..." % project_path)
        project = self.get_project(project_path)
        project.render(format=format, output_dir=output_dir)

    def get_python_runtime(self, version=None, python_runtime=None):
        if version is None:
            version = "%d.%d" % (sys.version_info.major, sys.version_info.minor)
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
