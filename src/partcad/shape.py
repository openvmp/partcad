#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.

import cadquery as cq
import build123d as b3d

from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
import logging
import os
import tempfile

from .render import *


class Shape:
    def __init__(self, name):
        self.name = name
        self.shape = None
        self.compound = None

        # Leave the svg path empty to get it created on demand
        self.svg_path = None
        self.svg_url = None

    def get_wrapped(self):
        return self.shape

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
                import ocp_vscode as ov

                try:
                    ov.config.status()
                    logging.info('Visualizing in "OCP CAD Viewer"...')
                    # logging.debug(self.shape)
                    ov.show(shape)
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

    def _finalize_real(self, show_object, render_path=None, embedded=False):
        if not show_object is None:
            self.show(show_object)

        if not embedded and self.shape is not None:
            if not render_path is None and not embedded:
                logging.info("Generating STL...")
                self.render_stl(render_path + "/" + self.name + ".stl")

                logging.info("Generating OBJ...")
                self.render_obj(render_path + "/" + self.name + ".obj")

                logging.info("Generating SVG...")
                self.render_svg(render_path + "/" + self.name + ".svg")

                logging.info("Generating PNG...")
                self.render_png(render_path + "/" + self.name + ".png")

    def render_stl(self, filepath=None, tolerance=0.5, angularTolerance=5.0):
        if filepath is None:
            filepath = self.path + "/part.stl"

        self.shape.exportStl(
            filepath,
            tolerance,
            angularTolerance,
        )

    def render_obj(self, filepath=None):
        if filepath is None:
            filepath = self.path + "/part.obj"

        try:
            vertices, triangles = self.shape.tessellate(0.5)

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

    def render_svg(self, filepath=None, opt=DEFAULT_RENDER_SVG_OPTS):
        if filepath is None:
            filepath = tempfile.mktemp(".svg")

        viewport_origin = (100, -100, 100)
        b3d_obj = self.get_build123d()
        visible, hidden = b3d_obj.project_to_viewport(
            viewport_origin,
        )
        max_dimension = max(
            *b3d.Compound(children=visible + hidden).bounding_box().size
        )
        exporter = b3d.ExportSVG(scale=100 / max_dimension)
        exporter.add_layer("Visible", fill_color=(224, 224, 48))
        # exporter.add_layer(
        #     "Hidden", line_color=(99, 99, 99), line_type=b3d.LineType.ISO_DOT
        # )
        exporter.add_shape(visible, layer="Visible", reverse_wires=False)
        # exporter.add_shape(hidden, layer="Hidden")
        exporter.write(filepath)

        self.svg_path = filepath

    def _get_svg_path(self):
        if self.svg_path is None:
            self.render_svg()
        return self.svg_path

    def _get_svg_url(self):
        if self.svg_url is None:
            svg_path = self._get_svg_path()
            # TODO(clairbee): implement a complex logic to get url from path
            self.svg_url = "./part.svg"
        return self.svg_url

    def render_png(
        self,
        project=None,
        filepath=None,
        width=None,
        height=None,
    ):
        if (
            not project is None
            and "render" in project.config_obj
            and not project.config_obj["render"] is None
        ):
            render_opts = project.config_obj["render"]
        else:
            render_opts = {}

        if "png" in render_opts and not render_opts["png"] is None:
            if isinstance(render_opts["png"], str):
                png_opts = {"prefix": render_opts["png"]}
            else:
                png_opts = render_opts["png"]
        else:
            png_opts = {}

        # Using the project's config defaults if any
        if filepath is None:
            if "prefix" in png_opts and not png_opts["prefix"] is None:
                filepath = os.path.join(png_opts["prefix"], self.name + ".png")
            else:
                filepath = self.name + ".png"

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
        logging.info("Rendering: %s" % filepath)
        svg_path = self._get_svg_path()

        # Render the raster image
        drawing = svg2rlg(svg_path)
        scale_width = float(width) / float(drawing.width)
        scale_height = float(height) / float(drawing.height)
        scale = min(scale_width, scale_height)
        drawing.scale(scale, scale)
        drawing.width *= scale
        drawing.height *= scale
        renderPM.drawToFile(drawing, filepath, fmt="PNG")

    def render_txt(self, filepath=None):
        if filepath is None:
            filepath = self.path + "/bom.txt"

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
