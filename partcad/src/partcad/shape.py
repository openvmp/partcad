#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.

import cadquery as cq
import build123d as b3d

import importlib
import logging
import os
import tempfile

from .render import *
from .plugins import *
from .shape_config import ShapeConfiguration


class Shape(ShapeConfiguration):
    name: str
    svg_path: str
    svg_url: str
    # shape: None | b3d.TopoDS_Shape | OCP.TopoDS.TopoDS_Solid

    def __init__(self, config):
        super().__init__(config)
        self.shape = None
        self.compound = None

        # Leave the svg path empty to get it created on demand
        self.svg_path = None
        self.svg_url = None

    def set_shape(self, shape):
        self.shape = shape

    def get_wrapped(self):
        return self.get_shape()

    def get_cadquery(self) -> cq.Shape:
        cq_solid = cq.Solid.makeBox(1, 1, 1)
        cq_solid.wrapped = self.get_wrapped()
        return cq_solid

    def get_build123d(self) -> b3d.Solid:
        b3d_solid = b3d.Solid.make_box(1, 1, 1)
        b3d_solid.wrapped = self.get_wrapped()
        return b3d_solid

    def show(self, show_object=None):
        shape = self.get_wrapped()
        if shape is not None:
            if show_object is None:
                ocp_vscode = importlib.import_module("ocp_vscode")
                if ocp_vscode is None:
                    logging.warn(
                        'Failed to load "ocp_vscode". Giving up on connection to VS Code.'
                    )
                else:
                    try:
                        # ocp_vscode.config.status()
                        logging.info('Visualizing in "OCP CAD Viewer"...')
                        # logging.debug(self.shape)
                        ocp_vscode.show(shape, progress=None)
                    except Exception as e:
                        logging.warning(e)
                        logging.warning(
                            'No VS Code or "OCP CAD Viewer" extension detected.'
                        )

            if show_object is not None:
                show_object(
                    shape,
                    options={},
                )

    def _finalize_real(self, show_object):
        if not show_object is None:
            self.show(show_object)

    def render_svg_somewhere(self, project=None, filepath=None):
        """Renders an SVG file somewhere and ignore the project settings"""
        if filepath is None:
            filepath = tempfile.mktemp(".svg")

        cq_obj = self.get_cadquery()
        cq_obj = cq_obj.rotate((0, 0, 0), (1, -1, 0.75), 180)
        cq.exporters.export(cq_obj, filepath, opt=DEFAULT_RENDER_SVG_OPTS)

        self.svg_path = filepath

    def _get_svg_path(self, project):
        if self.svg_path is None:
            self.render_svg_somewhere(project, None)
        return self.svg_path

    def render_getopts(
        self,
        kind,
        extension,
        project=None,
        filepath=None,
    ):
        if not project is None:
            render_opts = project.config_obj["render"]
        else:
            render_opts = {}

        if kind in render_opts and not render_opts[kind] is None:
            if isinstance(render_opts[kind], str):
                opts = {"prefix": render_opts[kind]}
            else:
                opts = render_opts[kind]
        else:
            opts = {}

        # Using the project's config defaults if any
        if filepath is None:
            if "prefix" in opts and not opts["prefix"] is None:
                filepath = os.path.join(opts["prefix"], self.name + extension)
            else:
                filepath = self.name + extension

            # Check if the format specific section of the config (e.g. "png")
            # provides a relative path and there is output dir in cmd line or
            # the generic section of rendering options in the config.
            if not os.path.isabs(filepath):
                if "output_dir" in render_opts:
                    filepath = os.path.join(render_opts["output_dir"], filepath)
                elif not project is None:
                    filepath = os.path.join(project.config_dir, filepath)

        logging.info("Rendering: %s" % filepath)

        return opts, filepath

    def render_svg(
        self,
        project=None,
        filepath=None,
    ):
        _, filepath = self.render_getopts("svg", ".svg", project, filepath)
        self.render_svg_somewhere(project, filepath)

    def render_png(
        self,
        project=None,
        filepath=None,
        width=None,
        height=None,
    ):
        if not plugins.export_png.is_supported():
            logging.error("Export to PNG is not supported")
            return

        png_opts, filepath = self.render_getopts("png", ".png", project, filepath)

        if width is None:
            if "width" in png_opts and not png_opts["width"] is None:
                width = png_opts["width"]
            else:
                width = DEFAULT_RENDER_WIDTH
        if height is None:
            if "height" in png_opts and not png_opts["height"] is None:
                height = png_opts["height"]
            else:
                height = DEFAULT_RENDER_HEIGHT

        # Render the vector image
        svg_path = self._get_svg_path(project)

        plugins.export_png.export(project, svg_path, width, height, filepath)

    def render_step(
        self,
        project=None,
        filepath=None,
    ):
        step_opts, filepath = self.render_getopts("step", ".step", project, filepath)

        cq_obj = self.get_cadquery()
        if not project is None:
            project.ctx.ensure_dirs_for_file(filepath)
        cq.exporters.export(cq_obj, filepath)

    def render_stl(
        self,
        project=None,
        filepath=None,
        tolerance=None,
    ):
        stl_opts, filepath = self.render_getopts("stl", ".stl", project, filepath)

        cq_obj = self.get_cadquery()
        if not project is None:
            project.ctx.ensure_dirs_for_file(filepath)
        cq.exporters.export(
            cq_obj,
            filepath,
        )

    def render_3mf(
        self,
        project=None,
        filepath=None,
        tolerance=None,
        angularTolerance=None,
    ):
        threemf_opts, filepath = self.render_getopts("3mf", ".3mf", project, filepath)

        if tolerance is None:
            if "tolerance" in threemf_opts and not threemf_opts["tolerance"] is None:
                tolerance = threemf_opts["tolerance"]
            else:
                tolerance = 0.1

        if angularTolerance is None:
            if (
                "angularTolerance" in threemf_opts
                and not threemf_opts["angularTolerance"] is None
            ):
                angularTolerance = threemf_opts["angularTolerance"]
            else:
                angularTolerance = 0.1

        cq_obj = self.get_cadquery()
        if not project is None:
            project.ctx.ensure_dirs_for_file(filepath)
        cq.exporters.export(
            cq_obj,
            filepath,
            tolerance=tolerance,
            angularTolerance=angularTolerance,
        )

    def render_threejs(
        self,
        project=None,
        filepath=None,
        tolerance=None,
        angularTolerance=None,
    ):
        threejs_opts, filepath = self.render_getopts(
            "threejs", ".json", project, filepath
        )

        if tolerance is None:
            if "tolerance" in threejs_opts and not threejs_opts["tolerance"] is None:
                tolerance = threejs_opts["tolerance"]
            else:
                tolerance = 0.1

        if angularTolerance is None:
            if (
                "angularTolerance" in threejs_opts
                and not threejs_opts["angularTolerance"] is None
            ):
                angularTolerance = threejs_opts["angularTolerance"]
            else:
                angularTolerance = 0.1

        cq_obj = self.get_cadquery()
        if not project is None:
            project.ctx.ensure_dirs_for_file(filepath)
        cq.exporters.export(
            cq_obj,
            filepath,
            tolerance=tolerance,
            angularTolerance=angularTolerance,
            exportType=cq.exporters.ExportTypes.TJS,
        )

    def render_obj(
        self,
        project=None,
        filepath=None,
        tolerance=None,
        angularTolerance=None,
    ):
        obj_opts, filepath = self.render_getopts("obj", ".obj", project, filepath)

        if tolerance is None:
            if "tolerance" in obj_opts and not obj_opts["tolerance"] is None:
                tolerance = obj_opts["tolerance"]
            else:
                tolerance = 0.1

        if angularTolerance is None:
            if (
                "angularTolerance" in obj_opts
                and not obj_opts["angularTolerance"] is None
            ):
                angularTolerance = obj_opts["angularTolerance"]
            else:
                angularTolerance = 0.1

        cq_obj = self.get_cadquery()

        try:
            vertices, triangles = cq_obj.tessellate(tolerance, angularTolerance)

            with open(filepath, "w") as f:
                f.write("# OBJ file\n")
                for v in vertices:
                    f.write("v %.4f %.4f %.4f\n" % (v.x, v.y, v.z))
                for p in triangles:
                    f.write("f")
                    for i in p:
                        f.write(" %d" % (i + 1))
                    f.write("\n")
        except:
            logging.error("Exception while exporting to " + filepath)

    def render_txt(self, project=None, filepath=None):
        if filepath is None:
            filepath = self.path + "/bom.txt"

        if not project is None:
            project.ctx.ensure_dirs_for_file(filepath)
        file = open(filepath, "w+")
        file.write("BoM:\n")
        self._render_txt_real(file)
        file.close()

    def render_markdown(self, filepath):
        if filepath is None:
            filepath = self.path + "/README.md"

        bom_file = open(filepath, "w+")
        bom_file.write(
            "# "
            + self.name
            + "\n"
            + "## Bill of Materials\n"
            + "| Part | Count* | Vendor | SKU | Preview |\n"
            + "| -- | -- | -- | -- | -- |\n"
        )
        self._render_markdown_real(bom_file)
        bom_file.write(
            """
(\\*) The `Count` field is the number of SKUs to be ordered.
It already takes into account the number of items per SKU.
            """
        )
        bom_file.close()
