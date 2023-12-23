#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.

from . import project_config
from . import part_factory_step as pfs
from . import part_factory_cadquery as pfc
from . import assembly_factory_python as afp


class Project(project_config.Configuration):
    def __init__(self, ctx, path):
        super().__init__(path)
        self.ctx = ctx
        self.path = path

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

    def get_part_config(self, part_name):
        if not part_name in self.part_configs:
            return None
        return self.part_configs[part_name]

    def get_part(self, part_name):
        if not part_name in self.parts:
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

            if not "type" in part_config or part_config["type"] == "cadquery":
                print("Initializing CadQuery part: %s..." % part_name)
                pfc.PartFactoryCadquery(self.ctx, self, part_config)
            elif part_config["type"] == "step":
                print("Initializing STEP part: %s..." % part_name)
                pfs.PartFactoryStep(self.ctx, self, part_config)
            else:
                print(
                    "Invalid repository type encountered: %s: %s"
                    % (part_name, part_config)
                )
                return None

            # Since factories do not return status codes, we need to verify
            # whether they have produced the expected product or not
            # TODO(clairbee): reconsider returning status from the factories
            if not part_name in self.parts:
                print("Failed to instantiate the part: %s" % part_config)
                return None

        return self.parts[part_name]

    def get_assembly_config(self, assembly_name):
        if not assembly_name in self.assembly_configs:
            return None
        return self.assembly_configs[assembly_name]

    def get_assembly(self, assembly_name):
        if not assembly_name in self.assemblies:
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

            afp.AssemblyFactoryPython(self.ctx, self, assembly_config)

            # Since factories do not return status codes, we need to verify
            # whether they have produced the expected product or not
            # TODO(clairbee): reconsider returning status from the factories
            if not assembly_name in self.assemblies:
                print("Failed to instantiate the assembly: %s" % assembly_config)
                return None

        return self.assemblies[assembly_name]

    def render(self):
        print("Rendering the project: ", self.path)
        if not "render" in self.config_obj:
            return
        render = self.config_obj["render"]

        parts = {}
        if "parts" in self.config_obj:
            parts = self.config_obj["parts"].keys()
        assemblies = {}
        if "assemblies" in self.config_obj:
            assemblies = self.config_obj["assemblies"].keys()

        if "png" in render:
            print("Rendering PNG...")
            if isinstance(render["png"], str):
                render_path = render["png"]
                render_width = None
                render_height = None
            else:
                png = render["png"]
                render_path = png["prefix"]
                render_width = png["width"]
                render_height = png["height"]

            for part_name in parts:
                part = self.get_part(part_name)
                if not part is None:
                    part.render_png(
                        render_path + part_name + ".png",
                        width=render_width,
                        height=render_height,
                    )
            for assembly_name in assemblies:
                assembly = self.get_assembly(assembly_name)
                if not assembly is None:
                    assembly.render_png(
                        render_path + assembly_name + ".png",
                        width=render_width,
                        height=render_height,
                    )
