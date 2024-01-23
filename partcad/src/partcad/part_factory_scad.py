#
# OpenVMP, 2024
#
# Author: Roman Kuzmenko
# Created: 2024-01-06
#
# Licensed under Apache License, Version 2.0.
#

import os
import shutil
import subprocess
import tempfile

import build123d as b3d
from . import part_factory_file as pff


class PartFactoryScad(pff.PartFactoryFile):
    def __init__(self, ctx, project, part_config):
        super().__init__(ctx, project, part_config, extension=".scad")
        # Complement the config object here if necessary
        self._create(part_config)

        self.project_dir = project.config_dir

    def instantiate(self, part):
        scad_path = shutil.which("openscad")
        if scad_path is None:
            raise Exception(
                "OpenSCAD executable is not found. Please, install OpenSCAD first."
            )

        stl_path = tempfile.mktemp(".stl")
        p = subprocess.run(
            [scad_path, "--export-format", "binstl", "-o", stl_path, self.path],
            capture_output=True,
        )

        shape = b3d.Mesher().read(stl_path)[0].wrapped
        os.unlink(stl_path)

        part.set_shape(shape)

        self.ctx.stats_parts_instantiated += 1
