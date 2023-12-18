#!/usr/bin/env python3
#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.

import ocp_vscode as ov
import cadquery as cq

import cairosvg

DEFAULT_EXPORT_SVQ_OPTS = {
    "width": 1024,
    "height": 320,
    "showAxes": False,
    "projectionDir": [0.5, 0.25, 0.5],
    "strokeWidth": 1.0,
    "strokeColor": [64, 192, 64],
    "hiddenColor": [32, 64, 32],
    "showHidden": False,
}


class Shape:
    def __init__(self, name):
        self.name = name

        # Leave the svg path empty to get it created on demand
        self.svg_path = None
        self.svg_url = None
        self.shape = None

    def _finalize_real(self, show_object, export_path=None):
        if self.shape is not None:
            try:
                ov.config.status()
                print('Visualizing in "OCP CAD Viewer"...')
                ov.show(self.shape)
            except Exception as e:
                print(e)
                print('No VS Code or "OCP CAD Viewer" extension detected.')

            if not export_path is None:
                # TODO(clairbee): remove compounding!!!
                self.shape = self.shape.toCompound()

                print("Generating STL...")
                self.export_stl(export_path + "/" + self.name + ".stl")

                print("Generating OBJ...")
                self.export_obj(export_path + "/" + self.name + ".obj")

                # TODO(clairbee): change the SVG params to drop the rotation step
                self.shape = self.shape.rotate((0, 0, 0), (1, 0, 0), -90)

                print("Generating SVG...")
                self.export_svg(export_path + "/" + self.name + ".svg")

                print("Generating PNG...")
                self.export_png(export_path + "/" + self.name + ".png")

            show_object(
                self.shape,
                options={},
            )

    def export_stl(self, filepath=None, tolerance=0.5, angularTolerance=5.0):
        if filepath is None:
            filepath = self.path + "/part.stl"

        self.shape.exportStl(
            filepath,
            tolerance,
            angularTolerance,
        )

    def export_obj(self, filepath=None):
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
            print("Exception while exporting to " + filepath)

    def export_svg(self, filepath, opt=DEFAULT_EXPORT_SVQ_OPTS):
        if filepath is None:
            filepath = self.path + "/part.svg"

        cq.exporters.export(
            self.shape,
            filepath,
            opt=opt,
        )

        self.svg_path = filepath

    def _get_svg_path(self):
        if self.svg_path is None:
            self.export_svg()
        return self.svg_path

    def _get_svg_url(self):
        if self.svg_url is None:
            svg_path = self._get_svg_path()
            # TODO(clairbee): implement a complex logic to get url from path
            self.svg_url = "./part.svg"
        return self.svg_url

    def export_png(
        self,
        filepath,
        width=DEFAULT_EXPORT_SVQ_OPTS["width"],
        height=DEFAULT_EXPORT_SVQ_OPTS["height"],
    ):
        if filepath is None:
            filepath = self.path + "/part.png"
        svg_path = self._get_svg_path()

        cairosvg.svg2png(
            url=svg_path,
            write_to=filepath,
            output_width=width,
            output_height=height,
        )

    def export_txt(self, filepath=None):
        if filepath is None:
            filepath = self.path + "/bom.txt"

        file = open(filepath, "w+")
        file.write("BoM:\n")
        self._export_txt_real(file)
        file.close()

    def export_markdown(self, filepath):
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
        self._export_markdown_real(bom_file)
        bom_file.write(
            """
(\\*) The `Count` field is the number of SKUs to be ordered.
It already takes into account the number of items per SKU.
            """
        )
        bom_file.close()
