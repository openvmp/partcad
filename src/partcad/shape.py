#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.

import cadquery as cq
import build123d as b3d

import cairosvg
import logging
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

    def get_cadquery(self) -> cq.Shape:
        cq_solid = cq.Solid.makeBox(1, 1, 1)
        cq_solid.wrapped = self.get_wrapped()
        return cq_solid

    def get_build123d(self) -> b3d.Shape:
        raise Exception("Part or Assembly must redefine get_build123d")

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

        cq_obj = self.get_cadquery()
        cq.exporters.export(
            cq_obj,
            filepath,
            opt=opt,
        )

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
        filepath,
        width=DEFAULT_RENDER_WIDTH,
        height=DEFAULT_RENDER_HEIGHT,
    ):
        if filepath is None:
            filepath = self.path + "/part.png"
        logging.info("Rendering: %s" % filepath)
        svg_path = self._get_svg_path()

        cairosvg.svg2png(
            url=svg_path,
            write_to=filepath,
            output_width=width,
            output_height=height,
        )

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
