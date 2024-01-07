#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.

import logging
import os

from . import project_config
from . import part_factory_scad as pfscad
from . import part_factory_step as pfs
from . import part_factory_stl as pfstl
from . import part_factory_3mf as pf3
from . import part_factory_cadquery as pfc
from . import part_factory_build123d as pfb
from . import assembly_factory_assy as afa


class Project(project_config.Configuration):
    def __init__(self, ctx, import_config_name, path):
        super().__init__(import_config_name, path)
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
        for part_name in self.part_configs:
            part_config = self.get_part_config(part_name)

            # Handle the case of the part being declared in the config
            # but not defined (a one liner like "part_name:").
            # TODO(clairbee): Revisit whether it's a bug or a feature
            #                 that this code allows to load undeclared scripts
            if part_config is None:
                part_config = {}

            # Instead of passing the name as a parameter,
            # enrich the configuration object
            # TODO(clairbee): reconsider passing the name as a parameter
            part_config["name"] = part_name

            if not "type" in part_config:
                raise Exception(
                    "ERROR: Part type is not specified: %s: %s"
                    % (part_name, part_config)
                )
            elif part_config["type"] == "cadquery":
                logging.info("Initializing CadQuery part: %s..." % part_name)
                pfc.PartFactoryCadquery(self.ctx, self, part_config)
            elif part_config["type"] == "build123d":
                logging.info("Initializing build123d part: %s..." % part_name)
                pfb.PartFactoryBuild123d(self.ctx, self, part_config)
            elif part_config["type"] == "step":
                logging.info("Initializing STEP part: %s..." % part_name)
                pfs.PartFactoryStep(self.ctx, self, part_config)
            elif part_config["type"] == "stl":
                logging.info("Initializing STL part: %s..." % part_name)
                pfstl.PartFactoryStl(self.ctx, self, part_config)
            elif part_config["type"] == "3mf":
                logging.info("Initializing 3mf part: %s..." % part_name)
                pf3.PartFactory3mf(self.ctx, self, part_config)
            elif part_config["type"] == "scad":
                logging.info("Initializing OpenSCAD part: %s..." % part_name)
                pfscad.PartFactoryScad(self.ctx, self, part_config)
            else:
                logging.error(
                    "Invalid part type encountered: %s: %s" % (part_name, part_config)
                )
                return None

    def get_part(self, part_name):
        if not part_name in self.parts:
            logging.error("Part not found: %s" % part_name)
            return None
        return self.parts[part_name]

    def get_assembly_config(self, assembly_name):
        if not assembly_name in self.assembly_configs:
            return None
        return self.assembly_configs[assembly_name]

    def init_assemblies(self):
        for assembly_name in self.assembly_configs:
            assembly_config = self.get_assembly_config(assembly_name)

            # Handle the case of the part being declared in the config
            # but not defined (a one liner like "part_name:").
            # TODO(clairbee): Revisit whether it's a bug or a feature
            #                 that this code allows to load undeclared scripts
            if assembly_config is None:
                assembly_config = {}

            # Instead of passing the name as a parameter,
            # enrich the configuration object
            # TODO(clairbee): reconsider passing the name as a parameter
            assembly_config["name"] = assembly_name

            if assembly_config["type"] == "assy":
                logging.info(
                    "Initializing AssemblyYAML assembly: %s..." % assembly_name
                )
                afa.AssemblyFactoryAssy(self.ctx, self, assembly_config)
            else:
                logging.error(
                    "Invalid assembly type encountered: %s: %s"
                    % (assembly_name, assembly_config)
                )
                return None

    def get_assembly(self, assembly_name):
        if not assembly_name in self.assemblies:
            logging.error("Assembly not found: %s" % assembly_name)
            return None
        return self.assemblies[assembly_name]

    def render(self, parts=None, assemblies=None):
        logging.info("Rendering the project: %s" % self.path)
        if not "render" in self.config_obj:
            return
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

        # See whether PNG is configured to be auto-rendered or not

        for part_name in parts:
            part = self.get_part(part_name)
            if not part is None:
                if "png" in render:
                    logging.info("Rendering PNG...")
                    part.render_png(project=self)
                if "step" in render:
                    logging.info("Rendering STEP...")
                    part.render_step(project=self)
                if "stl" in render:
                    logging.info("Rendering STL...")
                    part.render_stl(project=self)
                if "3mf" in render:
                    logging.info("Rendering 3MF...")
                    part.render_3mf(project=self)
                if "threejs" in render:
                    logging.info("Rendering ThreeJS...")
                    part.render_threejs(project=self)
        for assembly_name in assemblies:
            assembly = self.get_assembly(assembly_name)
            if not assembly is None:
                if "png" in render:
                    logging.info("Rendering PNG...")
                    assembly.render_png(project=self)
                if "step" in render:
                    logging.info("Rendering STEP...")
                    assembly.render_step(project=self)
                if "stl" in render:
                    logging.info("Rendering STL...")
                    assembly.render_stl(project=self)
                if "3mf" in render:
                    logging.info("Rendering 3MF...")
                    assembly.render_3mf(project=self)
                if "threejs" in render:
                    logging.info("Rendering ThreeJS...")
                    assembly.render_threejs(project=self)

            # See whether STEP is configured to be auto-rendered or not
