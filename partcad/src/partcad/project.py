#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.

import copy
import logging
import os
import ruamel.yaml
import typing

from . import project_config
from . import part
from . import part_config
from . import part_factory_scad as pfscad
from . import part_factory_step as pfs
from . import part_factory_stl as pfstl
from . import part_factory_3mf as pf3
from . import part_factory_cadquery as pfc
from . import part_factory_build123d as pfb
from . import part_factory_alias as pfa
from . import part_factory_enrich as pfe
from . import assembly
from . import assembly_config
from . import assembly_factory_alias as afalias
from . import assembly_factory_assy as afa


class Project(project_config.Configuration):
    def __init__(self, ctx, name, path):
        super().__init__(name, path)
        self.ctx = ctx

        # The 'path' parameter is the config filename or the directory
        # where 'partcad.yaml' is present.
        # 'self.path' has to be set to the directory name.
        dir_name = path
        if not os.path.isdir(dir_name):
            dir_name = os.path.dirname(os.path.abspath(dir_name))
        self.path = dir_name

        # self.part_configs contains the configs of all the parts in this project
        if "parts" in self.config_obj:
            self.part_configs = self.config_obj["parts"]
        else:
            self.part_configs = {}
        # self.parts contains all the initialized parts in this project
        self.parts = {}

        # self.assembly_configs contains the configs of all the assemblies in this project
        if "assemblies" in self.config_obj:
            self.assembly_configs = self.config_obj["assemblies"]
        else:
            self.assembly_configs = {}
        # self.assemblies contains all the initialized assemblies in this project
        self.assemblies = {}

        if "desc" in self.config_obj and isinstance(self.config_obj["desc"], str):
            self.desc = self.config_obj["desc"]
        else:
            self.desc = ""

        self.init_parts()
        self.init_assemblies()

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

    def init_part_by_config(self, config):
        part_name: str = config["name"]

        if not "type" in config:
            raise Exception(
                "ERROR: Part type is not specified: %s: %s" % (part_name, config)
            )
        elif config["type"] == "cadquery":
            logging.info("Initializing CadQuery part: %s..." % part_name)
            pfc.PartFactoryCadquery(self.ctx, self, config)
        elif config["type"] == "build123d":
            logging.info("Initializing build123d part: %s..." % part_name)
            pfb.PartFactoryBuild123d(self.ctx, self, config)
        elif config["type"] == "step":
            logging.info("Initializing STEP part: %s..." % part_name)
            pfs.PartFactoryStep(self.ctx, self, config)
        elif config["type"] == "stl":
            logging.info("Initializing STL part: %s..." % part_name)
            pfstl.PartFactoryStl(self.ctx, self, config)
        elif config["type"] == "3mf":
            logging.info("Initializing 3mf part: %s..." % part_name)
            pf3.PartFactory3mf(self.ctx, self, config)
        elif config["type"] == "scad":
            logging.info("Initializing OpenSCAD part: %s..." % part_name)
            pfscad.PartFactoryScad(self.ctx, self, config)
        elif config["type"] == "alias":
            logging.info("Initializing an alias: %s..." % part_name)
            pfa.PartFactoryAlias(self.ctx, self, config)
        elif config["type"] == "enrich":
            logging.info("Initializing an enrich: %s..." % part_name)
            pfe.PartFactoryEnrich(self.ctx, self, config)
        else:
            logging.error("Invalid part type encountered: %s: %s" % (part_name, config))
            return None

        # Initialize aliases if they are declared implicitly
        if "aliases" in config and not config["aliases"] is None:
            for alias in config["aliases"]:
                if ":" in part_name:
                    alias += part_name[part_name.index(":") :]
                alias_part_config = {
                    "type": "alias",
                    "name": alias,
                    "target": part_name,
                }
                alias_part_config = part_config.PartConfiguration.normalize(
                    alias, alias_part_config
                )
                pfa.PartFactoryAlias(self.ctx, self, alias_part_config)

    def get_part(self, part_name, func_params=None) -> part.Part:
        if func_params is None or not func_params:
            # Quick check if it's already available
            if part_name in self.parts:
                return self.parts[part_name]
            has_func_params = False
        else:
            has_func_params = True

        params: {str: typing.Any} = {}
        if ":" in part_name:
            has_name_params = True
            base_part_name = part_name.splt(":")[0]
            part_name_params_string = part_name.split(":")[1]

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
            # This is just a regular part name, no params
            if not part_name in self.parts:
                logging.error("Part '%s' not found in '%s'", part_name, self.name)
                return None
            return self.parts[part_name]

        if not base_part_name in self.parts:
            logging.error("Base part '%s' not found in '%s'", base_part_name, self.name)
            return None
        logging.info("Found the base part: %s" % base_part_name)

        # Now we have the original part name and the complete set of parameters
        config = self.part_configs[base_part_name]
        if config is None:
            logging.error(
                "The config for the base part '%s' is not found in '%s'",
                base_part_name,
                self.name,
            )
            return None

        config = copy.deepcopy(config)
        if not "parameters" in config or config["parameters"] is None:
            logging.error(
                "Attempt to parametrize '%s' of '%s' which has no parameters",
                base_part_name,
                self.name,
            )
            return None

        # Determine the name we want this parameterized part to have
        result_name = base_part_name + ":"
        result_name += ",".join(map(lambda n: n + "=" + str(params[n]), sorted(params)))

        # Expand the config object so that the parameter values can be set
        config = part_config.PartConfiguration.normalize(result_name, config)
        config["orig_name"] = base_part_name

        # Fill in the parameter values
        param_name: str
        for param_name, param_value in params.items():
            if config["parameters"][param_name]["type"] == "string":
                config["parameters"][param_name]["default"] = str(param_value)
            elif config["parameters"][param_name]["type"] == "int":
                config["parameters"][param_name]["default"] = int(param_value)
            elif config["parameters"][param_name]["type"] == "float":
                config["parameters"][param_name]["default"] = float(param_value)
            elif config["parameters"][param_name]["type"] == "bool":
                if isinstance(param_value, str):
                    if param_value.lower() == "true":
                        config["parameters"][param_name]["default"] = True
                    else:
                        config["parameters"][param_name]["default"] = False
                else:
                    config["parameters"][param_name]["default"] = bool(param_value)

        # Now initialize the part
        self.init_part_by_config(config)

        # See if it worked
        if not result_name in self.parts:
            logging.error(
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
            self.init_assembly_by_config(config)

    def init_assembly_by_config(self, config):
        assembly_name: str = config["name"]

        if config["type"] == "assy":
            logging.info("Initializing AssemblyYAML assembly: %s..." % assembly_name)
            afa.AssemblyFactoryAssy(self.ctx, self, config)
        elif config["type"] == "alias":
            logging.info("Initializing alias assembly: %s..." % assembly_name)
            afalias.AssemblyFactoryAlias(self.ctx, self, config)
        else:
            logging.error(
                "Invalid assembly type encountered: %s: %s" % (assembly_name, config)
            )
            return None

    def get_assembly(self, assembly_name, _func_params=None) -> assembly.Assembly:
        # TODO(clairbee): handle assembly params

        if not assembly_name in self.assemblies:
            logging.error("Assembly not found: %s" % assembly_name)
            return None
        return self.assemblies[assembly_name]

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

    def _validate_path(self, path, extension) -> (bool, str, str):
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        root = self.config_dir
        if not os.path.isabs(root):
            root = os.path.abspath(root)

        if not path.startswith(root):
            logging.error("Can't add files outside of the package")
            return False, None, None

        path = path[len(root) :]
        if path[0] == os.path.sep:
            path = path[1:]

        name = path
        if name.endswith(".%s" % extension):
            name = name[: -len(extension) - 1]

        return True, path, name

    def _add_component(self, kind: str, path: str, section: str, ext_by_kind) -> bool:
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

        obj = {"type": kind}
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

    def add_part(self, kind: str, path: str) -> bool:
        logging.info("Adding the part %s of type %s" % (path, kind))
        ext_by_kind = {
            "cadquery": "py",
            "build123d": "py",
        }
        return self._add_component(kind, path, "parts", ext_by_kind)

    def add_assembly(self, kind: str, path: str) -> bool:
        logging.info("Adding the assembly %s of type %s" % (path, kind))
        ext_by_kind = {}
        return self._add_component(kind, path, "assemblies", ext_by_kind)

    def render(self, parts=None, assemblies=None, format=None, output_dir=None):
        logging.info("Rendering the project: %s" % self.path)

        # Override the default output_dir.
        # TODO(clairbee): pass the preference downstream without making a
        # persistent change.
        if not output_dir is None:
            self.config_obj["render"]["output_dir"] = output_dir
        render = self.config_obj["render"]

        # Enumerating all parts and assemblies
        if parts is None:
            parts = []
            if "parts" in self.config_obj:
                parts = self.config_obj["parts"].keys()
        if assemblies is None:
            assemblies = []
            if "assemblies" in self.config_obj:
                assemblies = self.config_obj["assemblies"].keys()

        # Determine which formats need to be rendered.
        # The format needs to be rendered either if it's mentioned in the config
        # or if it's explicitly requested in the params (e.g. comes from the
        # command line).
        if format is None and "svg" in render:
            render_svg = True
        elif not format is None and format == "svg":
            render_svg = True
        else:
            render_svg = False

        if format is None and "png" in render:
            render_png = True
        elif not format is None and format == "png":
            render_png = True
        else:
            render_png = False

        if format is None and "step" in render:
            render_step = True
        elif not format is None and format == "step":
            render_step = True
        else:
            render_step = False

        if format is None and "stl" in render:
            render_stl = True
        elif not format is None and format == "stl":
            render_stl = True
        else:
            render_stl = False

        if format is None and "3mf" in render:
            render_3mf = True
        elif not format is None and format == "3mf":
            render_3mf = True
        else:
            render_3mf = False

        if format is None and "threejs" in render:
            render_threejs = True
        elif not format is None and format == "threejs":
            render_threejs = True
        else:
            render_threejs = False

        if format is None and "obj" in render:
            render_obj = True
        elif not format is None and format == "obj":
            render_obj = True
        else:
            render_obj = False

        # Render
        for part_name in parts:
            part = self.get_part(part_name)
            if not part is None:
                if render_svg:
                    logging.info("Rendering SVG...")
                    part.render_svg(project=self)
                if render_png:
                    logging.info("Rendering PNG...")
                    part.render_png(project=self)
                if render_step:
                    logging.info("Rendering STEP...")
                    part.render_step(project=self)
                if render_stl:
                    logging.info("Rendering STL...")
                    part.render_stl(project=self)
                if render_3mf:
                    logging.info("Rendering 3MF...")
                    part.render_3mf(project=self)
                if render_threejs:
                    logging.info("Rendering ThreeJS...")
                    part.render_threejs(project=self)
                if render_obj:
                    logging.info("Rendering OBJ...")
                    part.render_obj(project=self)
        for assembly_name in assemblies:
            assembly = self.get_assembly(assembly_name)
            if not assembly is None:
                if render_svg:
                    logging.info("Rendering SVG...")
                    assembly.render_svg(project=self)
                if render_png:
                    logging.info("Rendering PNG...")
                    assembly.render_png(project=self)
                if render_step:
                    logging.info("Rendering STEP...")
                    assembly.render_step(project=self)
                if render_stl:
                    logging.info("Rendering STL...")
                    assembly.render_stl(project=self)
                if render_3mf:
                    logging.info("Rendering 3MF...")
                    assembly.render_3mf(project=self)
                if render_threejs:
                    logging.info("Rendering ThreeJS...")
                    assembly.render_threejs(project=self)
                if render_obj:
                    logging.info("Rendering OBJ...")
                    assembly.render_obj(project=self)
