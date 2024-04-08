#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.

import asyncio
import copy
import os

# from pprint import pformat
import ruamel.yaml
import threading
import typing

from . import consts
from . import factory
from . import logging as pc_logging
from . import project_config
from . import part
from . import part_config
from . import part_factory_scad as pfscad
from . import part_factory_step as pfs
from . import part_factory_stl as pfstl
from . import part_factory_3mf as pf3
from .part_factory_ai_cadquery import PartFactoryAiCadquery
from .part_factory_ai_build123d import PartFactoryAiBuild123d
from .part_factory_ai_openscad import PartFactoryAiScad
from . import part_factory_cadquery as pfc
from . import part_factory_build123d as pfb
from . import part_factory_alias as pfa
from . import part_factory_enrich as pfe
from . import assembly
from . import assembly_config
from . import assembly_factory_alias as afalias
from . import assembly_factory_assy as afa
from .render import render_cfg_merge


class Project(project_config.Configuration):

    class PartLock(object):
        def __init__(self, prj, part_name: str):
            if not part_name in prj.part_locks:
                prj.part_locks[part_name] = threading.Lock()
            self.lock = prj.part_locks[part_name]

        def __enter__(self, *_args):
            self.lock.acquire()

        def __exit__(self, *_args):
            self.lock.release()

    class AssemblyLock(object):
        def __init__(self, prj, assembly_name: str):
            if not assembly_name in prj.assembly_locks:
                prj.assembly_locks[assembly_name] = threading.Lock()
            self.lock = prj.assembly_locks[assembly_name]

        def __enter__(self, *_args):
            self.lock.acquire()

        def __exit__(self, *_args):
            self.lock.release()

    def __init__(self, ctx, name, path):
        super().__init__(name, path)
        self.ctx = ctx

        # Protect the critical sections from access in different threads
        self.lock = threading.Lock()

        # The 'path' parameter is the config filename or the directory
        # where 'partcad.yaml' is present.
        # 'self.path' has to be set to the directory name.
        dir_name = path
        if not os.path.isdir(dir_name):
            dir_name = os.path.dirname(os.path.abspath(dir_name))
        self.path = dir_name

        # self.part_configs contains the configs of all the parts in this project
        if "parts" in self.config_obj and not self.config_obj["parts"] is None:
            self.part_configs = self.config_obj["parts"]
        else:
            self.part_configs = {}
        # self.parts contains all the initialized parts in this project
        self.parts = {}
        self.part_locks = {}

        # self.assembly_configs contains the configs of all the assemblies in this project
        if (
            "assemblies" in self.config_obj
            and not self.config_obj["assemblies"] is None
        ):
            self.assembly_configs = self.config_obj["assemblies"]
        else:
            self.assembly_configs = {}
        # self.assemblies contains all the initialized assemblies in this project
        self.assemblies = {}
        self.assembly_locks = {}

        if (
            "desc" in self.config_obj
            and not self.config_obj["desc"] is None
            and isinstance(self.config_obj["desc"], str)
        ):
            self.desc = self.config_obj["desc"]
        else:
            self.desc = ""

        self.init_parts()
        self.init_assemblies()

    # TODO(clairbee): Implement get_cover()
    # def get_cover(self):
    #     if not "cover" in self.config_obj or self.config_obj["cover"] is None:
    #         return None
    #     if isinstance(self.config_obj["cover"], str):
    #         return os.path.join(self.config_dir, self.config_obj["cover"])
    #     elif "package" in self.config_obj["cover"]:
    #         return self.ctx.get_project(
    #             self.path + "/" + self.config_obj["cover"]["package"]
    #         ).get_cover()

    def get_child_project_names(self):
        children = list()
        subfolders = [f.name for f in os.scandir(self.config_dir) if f.is_dir()]
        for subdir in list(subfolders):
            if os.path.exists(
                os.path.join(
                    self.config_dir,
                    subdir,
                    consts.DEFAULT_PACKAGE_CONFIG,
                )
            ):
                children.append(self.name + "/" + subdir)

        if (
            "import" in self.config_obj
            and not self.config_obj["import"] is None
        ):
            children.extend(
                list(
                    map(
                        lambda project_name: self.name + "/" + project_name,
                        self.config_obj["import"],
                    )
                )
            )
        return children

    def get_part_config(self, part_name):
        if not part_name in self.part_configs:
            return None
        return self.part_configs[part_name]

    def init_parts(self):
        if self.part_configs is None:
            return

        for part_name in self.part_configs:
            config = self.get_part_config(part_name)
            config = part_config.PartConfiguration.normalize(part_name, config)
            self.init_part_by_config(config)

    def init_part_by_config(self, config, source_project=None):
        if source_project is None:
            source_project = self

        part_name: str = config["name"]

        if not "type" in config:
            raise Exception(
                "ERROR: Part type is not specified: %s: %s"
                % (part_name, config)
            )
        elif config["type"] == "ai-cadquery":
            PartFactoryAiCadquery(self.ctx, source_project, self, config)
        elif config["type"] == "ai-build123d":
            PartFactoryAiBuild123d(self.ctx, source_project, self, config)
        elif config["type"] == "ai-openscad":
            PartFactoryAiScad(self.ctx, source_project, self, config)
        elif config["type"] == "cadquery":
            pfc.PartFactoryCadquery(self.ctx, source_project, self, config)
        elif config["type"] == "build123d":
            pfb.PartFactoryBuild123d(self.ctx, source_project, self, config)
        elif config["type"] == "step":
            pfs.PartFactoryStep(self.ctx, source_project, self, config)
        elif config["type"] == "stl":
            pfstl.PartFactoryStl(self.ctx, source_project, self, config)
        elif config["type"] == "3mf":
            pf3.PartFactory3mf(self.ctx, source_project, self, config)
        elif config["type"] == "scad":
            pfscad.PartFactoryScad(self.ctx, source_project, self, config)
        elif config["type"] == "alias":
            pfa.PartFactoryAlias(self.ctx, source_project, self, config)
        elif config["type"] == "enrich":
            pfe.PartFactoryEnrich(self.ctx, source_project, self, config)
        else:
            pc_logging.error(
                "Invalid part type encountered: %s: %s" % (part_name, config)
            )
            return None

        # Initialize aliases if they are declared implicitly
        if "aliases" in config and not config["aliases"] is None:
            for alias in config["aliases"]:
                if ";" in part_name:
                    # Copy parameters
                    alias += part_name[part_name.index(";") :]
                alias_part_config = {
                    "type": "alias",
                    "name": alias,
                    "source": ":" + part_name,
                }
                alias_part_config = part_config.PartConfiguration.normalize(
                    alias, alias_part_config
                )
                pfa.PartFactoryAlias(
                    self.ctx, source_project, self, alias_part_config
                )

    def get_part(self, part_name, func_params=None) -> part.Part:
        if func_params is None or not func_params:
            has_func_params = False
        else:
            has_func_params = True

        params: {str: typing.Any} = {}
        if ";" in part_name:
            has_name_params = True
            base_part_name = part_name.split(";")[0]
            part_name_params_string = part_name.split(";")[1]

            for kv in part_name_params_string.split[","]:
                k, v = kv.split("")
                params[k] = v
        else:
            has_name_params = False
            base_part_name = part_name

        if has_func_params:
            params = {**params, **func_params}
            has_name_params = True

        if not has_name_params:
            result_name = part_name
        else:
            # Determine the name we want this parameterized part to have
            result_name = base_part_name + ";"
            result_name += ",".join(
                map(lambda n: n + "=" + str(params[n]), sorted(params))
            )

        self.lock.acquire()

        # See if it's already available
        if result_name in self.parts and not self.parts[result_name] is None:
            p = self.parts[result_name]
            self.lock.release()
            return p

        with Project.PartLock(self, result_name):
            # Release the project lock, and continue with holding the part lock only
            self.lock.release()

            if not has_name_params:
                # This is just a regular part name, no params (part_name == result_name)
                if not part_name in self.part_configs:
                    # We don't know anything about such a part
                    pc_logging.error(
                        "Part '%s' not found in '%s'", part_name, self.name
                    )
                    return None
                # This is not yet created (invalidated?)
                config = self.get_part_config(part_name)
                config = part_config.PartConfiguration.normalize(
                    part_name, config
                )
                self.init_part_by_config(config)

                if not part_name in self.parts or self.parts[part_name] is None:
                    pc_logging.error(
                        "Failed to instantiate a non-parametrized part %s"
                        % part_name
                    )
                return self.parts[part_name]

            # This part has params (part_name != result_name)
            if not base_part_name in self.parts:
                pc_logging.error(
                    "Base part '%s' not found in '%s'",
                    base_part_name,
                    self.name,
                )
                return None
            pc_logging.debug("Found the base part: %s" % base_part_name)

            # Now we have the original part name and the complete set of parameters
            config = self.part_configs[base_part_name]
            if config is None:
                pc_logging.error(
                    "The config for the base part '%s' is not found in '%s'",
                    base_part_name,
                    self.name,
                )
                return None

            config = copy.deepcopy(config)
            if (
                not "parameters" in config or config["parameters"] is None
            ) and (config["type"] != "enrich"):
                pc_logging.error(
                    "Attempt to parametrize '%s' of '%s' which has no parameters: %s",
                    base_part_name,
                    self.name,
                    str(config),
                )
                return None

            # Expand the config object so that the parameter values can be set
            config = part_config.PartConfiguration.normalize(
                result_name, config
            )
            config["orig_name"] = base_part_name

            # Fill in the parameter values
            param_name: str
            if "parameters" in config and not config["parameters"] is None:
                # Filling "parameters"
                for param_name, param_value in params.items():
                    if config["parameters"][param_name]["type"] == "string":
                        config["parameters"][param_name]["default"] = str(
                            param_value
                        )
                    elif config["parameters"][param_name]["type"] == "int":
                        config["parameters"][param_name]["default"] = int(
                            param_value
                        )
                    elif config["parameters"][param_name]["type"] == "float":
                        config["parameters"][param_name]["default"] = float(
                            param_value
                        )
                    elif config["parameters"][param_name]["type"] == "bool":
                        if isinstance(param_value, str):
                            if param_value.lower() == "true":
                                config["parameters"][param_name][
                                    "default"
                                ] = True
                            else:
                                config["parameters"][param_name][
                                    "default"
                                ] = False
                        else:
                            config["parameters"][param_name]["default"] = bool(
                                param_value
                            )
            else:
                # Filling "with"
                if not "with" in config:
                    config["with"] = {}
                for param_name, param_value in params.items():
                    config["with"][param_name] = param_value

            # Now initialize the part
            pc_logging.debug(
                "Initializing a parametrized part: %s" % result_name
            )
            # pc_logging.debug(
            #     "Initializing a parametrized part using the following config: %s"
            #     % pformat(config)
            # )
            self.init_part_by_config(config)

            # See if it worked
            if not result_name in self.parts:
                pc_logging.error(
                    "Failed to instantiate parameterized part '%s' in '%s'",
                    result_name,
                    self.name,
                )
                return None

            return self.parts[result_name]

    def get_assembly_config(self, assembly_name):
        if not assembly_name in self.assembly_configs:
            return None
        return self.assembly_configs[assembly_name]

    def init_assemblies(self):
        if self.assembly_configs is None:
            return

        for assembly_name in self.assembly_configs:
            config = self.get_assembly_config(assembly_name)
            config = assembly_config.AssemblyConfiguration.normalize(
                assembly_name, config
            )
            factory.instantiate("assembly", self.ctx, self, config)

    def get_assembly(
        self, assembly_name, func_params=None
    ) -> assembly.Assembly:
        if func_params is None or not func_params:
            has_func_params = False
        else:
            has_func_params = True

        params: {str: typing.Any} = {}
        if ";" in assembly_name:
            has_name_params = True
            base_assembly_name = assembly_name.split(";")[0]
            assembly_name_params_string = assembly_name.split(";")[1]

            for kv in assembly_name_params_string.split[","]:
                k, v = kv.split("")
                params[k] = v
        else:
            has_name_params = False
            base_assembly_name = assembly_name

        if has_func_params:
            params = {**params, **func_params}
            has_name_params = True

        if not has_name_params:
            result_name = assembly_name
        else:
            # Determine the name we want this parameterized assembly to have
            result_name = base_assembly_name + ";"
            result_name += ",".join(
                map(lambda n: n + "=" + str(params[n]), sorted(params))
            )

        self.lock.acquire()

        # See if it's already available
        if (
            result_name in self.assemblies
            and not self.assemblies[result_name] is None
        ):
            p = self.assemblies[result_name]
            self.lock.release()
            return p

        with Project.AssemblyLock(self, result_name):
            # Release the project lock, and continue with holding the part lock only
            self.lock.release()

            if not has_name_params:
                # This is just a regular assembly name, no params (assembly_name == result_name)
                if not assembly_name in self.assembly_configs:
                    # We don't know anything about such an assembly
                    pc_logging.error(
                        "Assembly '%s' not found in '%s'",
                        assembly_name,
                        self.name,
                    )
                    return None
                # This is not yet created (invalidated?)
                config = self.get_assembly_config(assembly_name)
                config = assembly_config.AssemblyConfiguration.normalize(
                    assembly_name, config
                )
                factory.instantiate("assembly", self.ctx, self, config)

                if (
                    not assembly_name in self.assemblies
                    or self.assemblies[assembly_name] is None
                ):
                    pc_logging.error(
                        "Failed to instantiate a non-parametrized assembly %s"
                        % assembly_name
                    )
                return self.assemblies[assembly_name]

            # This assembly has params (part_name != result_name)
            if not base_assembly_name in self.assemblies:
                pc_logging.error(
                    "Base assembly '%s' not found in '%s'",
                    base_assembly_name,
                    self.name,
                )
                return None
            pc_logging.debug("Found the base assembly: %s" % base_assembly_name)

            # Now we have the original assembly name and the complete set of parameters
            config = self.assembly_configs[base_assembly_name]
            if config is None:
                pc_logging.error(
                    "The config for the base assembly '%s' is not found in '%s'",
                    base_assembly_name,
                    self.name,
                )
                return None

            config = copy.deepcopy(config)
            if (
                not "parameters" in config or config["parameters"] is None
            ) and (config["type"] != "enrich"):
                pc_logging.error(
                    "Attempt to parametrize '%s' of '%s' which has no parameters: %s",
                    base_assembly_name,
                    self.name,
                    str(config),
                )
                return None

            # Expand the config object so that the parameter values can be set
            config = assembly_config.AssemblyConfiguration.normalize(
                result_name, config
            )
            config["orig_name"] = base_assembly_name

            # Fill in the parameter values
            param_name: str
            if "parameters" in config and not config["parameters"] is None:
                # Filling "parameters"
                for param_name, param_value in params.items():
                    if config["parameters"][param_name]["type"] == "string":
                        config["parameters"][param_name]["default"] = str(
                            param_value
                        )
                    elif config["parameters"][param_name]["type"] == "int":
                        config["parameters"][param_name]["default"] = int(
                            param_value
                        )
                    elif config["parameters"][param_name]["type"] == "float":
                        config["parameters"][param_name]["default"] = float(
                            param_value
                        )
                    elif config["parameters"][param_name]["type"] == "bool":
                        if isinstance(param_value, str):
                            if param_value.lower() == "true":
                                config["parameters"][param_name][
                                    "default"
                                ] = True
                            else:
                                config["parameters"][param_name][
                                    "default"
                                ] = False
                        else:
                            config["parameters"][param_name]["default"] = bool(
                                param_value
                            )
            else:
                # Filling "with"
                if not "with" in config:
                    config["with"] = {}
                for param_name, param_value in params.items():
                    config["with"][param_name] = param_value

            # Now initialize the assembly
            pc_logging.debug(
                "Initializing a parametrized assembly: %s" % result_name
            )
            # pc_logging.debug(
            #     "Initializing a parametrized assembly using the following config: %s"
            #     % pformat(config)
            # )
            factory.instantiate("assembly", self.ctx, self, config)

            # See if it worked
            if not result_name in self.assemblies:
                pc_logging.error(
                    "Failed to instantiate parameterized assembly '%s' in '%s'",
                    result_name,
                    self.name,
                )
                return None

            return self.assemblies[result_name]

    def add_import(self, alias, location):
        if ":" in location:
            location_param = "url"
            if location.endswith(".tar.gz"):
                location_type = "tar"
            else:
                location_type = "git"
        else:
            location_param = "path"
            location_type = "local"

        yaml = ruamel.yaml.YAML()
        yaml.preserve_quotes = True
        with open(self.config_path) as fp:
            config = yaml.load(fp)
            fp.close()

        for elem in config:
            if elem == "import":
                imports = config["import"]
                imports[alias] = {
                    location_param: location,
                    "type": location_type,
                }
                break  # no need to iterate further
        with open(self.config_path) as fp:
            yaml.dump(config, fp)
            fp.close()

    def _validate_path(self, path, extension) -> tuple[bool, str, str]:
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        root = self.config_dir
        if not os.path.isabs(root):
            root = os.path.abspath(root)

        if not path.startswith(root):
            pc_logging.error("Can't add files outside of the package")
            return False, None, None

        path = path[len(root) :]
        if path[0] == os.path.sep:
            path = path[1:]

        name = path
        if name.endswith(".%s" % extension):
            name = name[: -len(extension) - 1]

        return True, path, name

    def _add_component(
        self,
        kind: str,
        path: str,
        section: str,
        ext_by_kind: dict[str, str],
        component_config,
    ) -> bool:
        if kind in ext_by_kind:
            ext = ext_by_kind[kind]
        else:
            ext = kind

        valid, path, name = self._validate_path(path, ext)
        if not valid:
            return False

        yaml = ruamel.yaml.YAML()
        yaml.preserve_quotes = True
        with open(self.config_path) as fp:
            config = yaml.load(fp)
            fp.close()

        obj = {"type": kind, **component_config}
        if name == path:
            obj["path"] = path

        found = False
        for elem in config:
            if elem == section:
                config_section = config[section]
                if config_section is None:
                    config_section = {}
                config_section[name] = obj
                config[section] = config_section
                found = True
                break  # no need to iterate further
        if not found:
            config[section] = {name: obj}

        with open(self.config_path, "w") as fp:
            yaml.dump(config, fp)
            fp.close()

        return True

    def add_part(self, kind: str, path: str, config={}) -> bool:
        pc_logging.info("Adding the part %s of type %s" % (path, kind))
        ext_by_kind = {
            "cadquery": "py",
            "build123d": "py",
            "ai-cadquery": "py",
            "ai-openscad": "scad",
        }
        return self._add_component(
            kind,
            path,
            "parts",
            ext_by_kind,
            config,
        )

    def add_assembly(self, kind: str, path: str, config={}) -> bool:
        pc_logging.info("Adding the assembly %s of type %s" % (path, kind))
        ext_by_kind = {}
        return self._add_component(
            kind,
            path,
            "assemblies",
            ext_by_kind,
            config,
        )

    def set_part_config(self, part_name, part_config):
        if "name" in part_config:
            del part_config["name"]
        if "orig_name" in part_config:
            del part_config["orig_name"]

        yaml = ruamel.yaml.YAML()
        yaml.preserve_quotes = True
        with open(self.config_path) as fp:
            config = yaml.load(fp)
            fp.close()

        if "parts" in config:
            parts = config["parts"]
            parts[part_name] = part_config
        else:
            config["parts"] = {part_name: part_config}

        with open(self.config_path, "w") as fp:
            yaml.dump(config, fp)
            fp.close()

    def update_part_config(
        self, part_name, part_config_update: dict[str, typing.Any]
    ):
        yaml = ruamel.yaml.YAML()
        yaml.preserve_quotes = True
        with open(self.config_path) as fp:
            config = yaml.load(fp)
            fp.close()

        if "parts" in config:
            parts = config["parts"]
            if part_name in parts:
                part_config = parts[part_name]
                for key, value in part_config_update.items():
                    part_config[key] = value

                with open(self.config_path, "w") as fp:
                    yaml.dump(config, fp)
                    fp.close()

    async def render_async(
        self, parts=None, assemblies=None, format=None, output_dir=None
    ):
        with pc_logging.Action("RenderPkg", self.name):
            # Override the default output_dir.
            # TODO(clairbee): pass the preference downstream without making a
            # persistent change.
            if not output_dir is None:
                self.config_obj["render"]["output_dir"] = output_dir

            if (
                "render" in self.config_obj
                and not self.config_obj["render"] is None
            ):
                render = self.config_obj["render"]
            else:
                render = {}

            # Enumerating all parts and assemblies
            if parts is None:
                parts = []
                if (
                    "parts" in self.config_obj
                    and not self.config_obj["parts"] is None
                ):
                    parts = self.config_obj["parts"].keys()
            if assemblies is None:
                assemblies = []
                if (
                    "assemblies" in self.config_obj
                    and not self.config_obj["assemblies"] is None
                ):
                    assemblies = self.config_obj["assemblies"].keys()

            # Render
            tasks = []
            for part_name in parts:
                part = self.get_part(part_name)
                if not part is None:
                    part_render = render
                    if (
                        "render" in part.config
                        and not part.config["render"] is None
                    ):
                        part_render = render_cfg_merge(
                            part_render, part.config["render"]
                        )

                    # Determine which formats need to be rendered.
                    # The format needs to be rendered either if it's mentioned in the config
                    # or if it's explicitly requested in the params (e.g. comes from the
                    # command line).
                    if format is None and "svg" in part_render:
                        render_svg = True
                    elif not format is None and format == "svg":
                        render_svg = True
                    else:
                        render_svg = False

                    if format is None and "png" in part_render:
                        render_png = True
                    elif not format is None and format == "png":
                        render_png = True
                    else:
                        render_png = False

                    if format is None and "step" in part_render:
                        render_step = True
                    elif not format is None and format == "step":
                        render_step = True
                    else:
                        render_step = False

                    if format is None and "stl" in part_render:
                        render_stl = True
                    elif not format is None and format == "stl":
                        render_stl = True
                    else:
                        render_stl = False

                    if format is None and "3mf" in part_render:
                        render_3mf = True
                    elif not format is None and format == "3mf":
                        render_3mf = True
                    else:
                        render_3mf = False

                    if format is None and "threejs" in part_render:
                        render_threejs = True
                    elif not format is None and format == "threejs":
                        render_threejs = True
                    else:
                        render_threejs = False

                    if format is None and "obj" in part_render:
                        render_obj = True
                    elif not format is None and format == "obj":
                        render_obj = True
                    else:
                        render_obj = False

                    if format is None and "gltf" in part_render:
                        render_gltf = True
                    elif not format is None and format == "gltf":
                        render_gltf = True
                    else:
                        render_gltf = False

                    if render_svg:
                        tasks.append(part.render_svg_async(self.ctx, self))
                    if render_png:
                        tasks.append(part.render_png_async(self.ctx, self))
                    if render_step:
                        tasks.append(part.render_step_async(self.ctx, self))
                    if render_stl:
                        tasks.append(part.render_stl_async(self.ctx, self))
                    if render_3mf:
                        tasks.append(part.render_3mf_async(self.ctx, self))
                    if render_threejs:
                        tasks.append(part.render_threejs_async(self.ctx, self))
                    if render_obj:
                        tasks.append(part.render_obj_async(self.ctx, self))
                    if render_gltf:
                        tasks.append(part.render_gltf_async(self.ctx, self))

            for assembly_name in assemblies:
                assembly = self.get_assembly(assembly_name)
                if not assembly is None:
                    assy_render = render
                    if (
                        "render" in assembly.config
                        and not assembly.config["render"] is None
                    ):
                        assy_render = render_cfg_merge(
                            assy_render, assembly.config["render"]
                        )

                    # Determine which formats need to be rendered.
                    # The format needs to be rendered either if it's mentioned in the config
                    # or if it's explicitly requested in the params (e.g. comes from the
                    # command line).
                    if format is None and "svg" in assy_render:
                        render_svg = True
                    elif not format is None and format == "svg":
                        render_svg = True
                    else:
                        render_svg = False

                    if format is None and "png" in assy_render:
                        render_png = True
                    elif not format is None and format == "png":
                        render_png = True
                    else:
                        render_png = False

                    if format is None and "step" in assy_render:
                        render_step = True
                    elif not format is None and format == "step":
                        render_step = True
                    else:
                        render_step = False

                    if format is None and "stl" in assy_render:
                        render_stl = True
                    elif not format is None and format == "stl":
                        render_stl = True
                    else:
                        render_stl = False

                    if format is None and "3mf" in assy_render:
                        render_3mf = True
                    elif not format is None and format == "3mf":
                        render_3mf = True
                    else:
                        render_3mf = False

                    if format is None and "threejs" in assy_render:
                        render_threejs = True
                    elif not format is None and format == "threejs":
                        render_threejs = True
                    else:
                        render_threejs = False

                    if format is None and "obj" in assy_render:
                        render_obj = True
                    elif not format is None and format == "obj":
                        render_obj = True
                    else:
                        render_obj = False

                    if format is None and "gltf" in assy_render:
                        render_gltf = True
                    elif not format is None and format == "gltf":
                        render_gltf = True
                    else:
                        render_gltf = False

                    if render_svg:
                        tasks.append(assembly.render_svg_async(self.ctx, self))
                    if render_png:
                        tasks.append(assembly.render_png_async(self.ctx, self))
                    if render_step:
                        tasks.append(assembly.render_step_async(self.ctx, self))
                    if render_stl:
                        tasks.append(assembly.render_stl_async(self.ctx, self))
                    if render_3mf:
                        tasks.append(assembly.render_3mf_async(self.ctx, self))
                    if render_threejs:
                        tasks.append(
                            assembly.render_threejs_async(self.ctx, self)
                        )
                    if render_obj:
                        tasks.append(assembly.render_obj_async(self.ctx, self))
                    if render_gltf:
                        tasks.append(assembly.render_gltf_async(self.ctx, self))

            await asyncio.gather(*tasks)

    def render(self, parts=None, assemblies=None, format=None, output_dir=None):
        asyncio.run(self.render_async(parts, assemblies, format, output_dir))
