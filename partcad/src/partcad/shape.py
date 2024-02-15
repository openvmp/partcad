#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.

import cadquery as cq
import build123d as b3d

import asyncio
import os
import shutil
import tempfile

from .render import *
from .plugins import *
from .shape_config import ShapeConfiguration
from . import logging as pc_logging
from . import sync_threads as pc_thread


class Shape(ShapeConfiguration):
    name: str
    desc: str
    svg_path: str
    svg_url: str
    # shape: None | b3d.TopoDS_Shape | OCP.TopoDS.TopoDS_Solid

    def __init__(self, config):
        super().__init__(config)
        self.shape = None
        self.compound = None

        # Leave the svg path empty to get it created on demand
        self.svg_lock = asyncio.Lock()
        self.svg_path = None
        self.svg_url = None

    async def get_wrapped(self):
        return await self.get_shape()

    async def get_cadquery(self) -> cq.Shape:
        cq_solid = cq.Solid.makeBox(1, 1, 1)
        cq_solid.wrapped = await self.get_wrapped()
        return cq_solid

    async def get_build123d(self) -> b3d.Solid:
        b3d_solid = b3d.Solid.make_box(1, 1, 1)
        b3d_solid.wrapped = await self.get_wrapped()
        return b3d_solid

    async def show_async(self, show_object=None):
        with pc_logging.Action("Show", self.project_name, self.name):
            shape = await self.get_wrapped()
            if shape is not None:
                if show_object is None:
                    import importlib

                    ocp_vscode = importlib.import_module("ocp_vscode")
                    if ocp_vscode is None:
                        pc_logging.warn(
                            'Failed to load "ocp_vscode". Giving up on connection to VS Code.'
                        )
                    else:
                        try:
                            # ocp_vscode.config.status()
                            pc_logging.info('Visualizing in "OCP CAD Viewer"...')
                            # pc_logging.debug(self.shape)
                            ocp_vscode.show(shape, progress=None)
                        except Exception as e:
                            pc_logging.warning(e)
                            pc_logging.warning(
                                'No VS Code or "OCP CAD Viewer" extension detected.'
                            )

                if show_object is not None:
                    show_object(
                        shape,
                        options={},
                    )

    def show(self, show_object=None):
        asyncio.run(self.show_async(show_object))

    async def render_svg_somewhere(self, project=None, filepath=None):
        """Renders an SVG file somewhere and ignore the project settings"""
        if filepath is None:
            filepath = tempfile.mktemp(".svg")

        cq_obj = await self.get_cadquery()

        def do_render_svg():
            nonlocal cq_obj, filepath
            cq_obj = cq_obj.rotate((0, 0, 0), (1, -1, 0.75), 180)
            cq.exporters.export(cq_obj, filepath, opt=DEFAULT_RENDER_SVG_OPTS)

        await pc_thread.run(do_render_svg)

        self.svg_path = filepath

    async def _get_svg_path(self, project):
        async with self.svg_lock:
            if self.svg_path is None:
                await self.render_svg_somewhere(project, None)
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

        pc_logging.debug("Rendering: %s" % filepath)

        return opts, filepath

    async def render_svg_async(
        self,
        project=None,
        filepath=None,
    ):
        with pc_logging.Action("RenderSVG", self.project_name, self.name):
            _, filepath = self.render_getopts("svg", ".svg", project, filepath)

            # This creates a temporary file, but it allows to reuse the file
            # with other consumers of self._get_svg_path()
            svg_path = await self._get_svg_path(project)
            shutil.copyfile(svg_path, filepath)

    def render_svg(
        self,
        project=None,
        filepath=None,
    ):
        asyncio.run(self.render_svg_async(project, filepath))

    async def render_png_async(
        self,
        project=None,
        filepath=None,
        width=None,
        height=None,
    ):
        with pc_logging.Action("RenderPNG", self.project_name, self.name):
            if not plugins.export_png.is_supported():
                pc_logging.error("Export to PNG is not supported")
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
            svg_path = await self._get_svg_path(project)

            def do_render_png():
                nonlocal project, svg_path, width, height, filepath
                plugins.export_png.export(project, svg_path, width, height, filepath)

            await pc_thread.run(do_render_png)

    def render_png(
        self,
        project=None,
        filepath=None,
        width=None,
        height=None,
    ):
        asyncio.run(self.render_png_async(project, filepath, width, height))

    async def render_step_async(
        self,
        project=None,
        filepath=None,
    ):
        with pc_logging.Action("RenderSTEP", self.project_name, self.name):
            step_opts, filepath = self.render_getopts(
                "step", ".step", project, filepath
            )

            cq_obj = await self.get_cadquery()

            def do_render_step():
                nonlocal project, filepath, cq_obj
                if not project is None:
                    project.ctx.ensure_dirs_for_file(filepath)
                cq.exporters.export(cq_obj, filepath)

            await pc_thread.run(do_render_step)

    def render_step(
        self,
        project=None,
        filepath=None,
    ):
        asyncio.run(self.render_step_async(project, filepath))

    async def render_stl_async(
        self,
        project=None,
        filepath=None,
        tolerance=None,
        angularTolerance=None,
    ):
        with pc_logging.Action("RenderSTL", self.project_name, self.name):
            stl_opts, filepath = self.render_getopts("stl", ".stl", project, filepath)

            if tolerance is None:
                if "tolerance" in stl_opts and not stl_opts["tolerance"] is None:
                    tolerance = stl_opts["tolerance"]
                else:
                    tolerance = 0.1

            if angularTolerance is None:
                if (
                    "angularTolerance" in stl_opts
                    and not stl_opts["angularTolerance"] is None
                ):
                    angularTolerance = stl_opts["angularTolerance"]
                else:
                    angularTolerance = 0.1

            cq_obj = await self.get_cadquery()

            def do_render_stl():
                nonlocal cq_obj, project, filepath, tolerance, angularTolerance
                if not project is None:
                    project.ctx.ensure_dirs_for_file(filepath)
                cq.exporters.export(
                    cq_obj,
                    filepath,
                    tolerance=tolerance,
                    angularTolerance=angularTolerance,
                )

            await pc_thread.run(do_render_stl)

    def render_stl(
        self,
        project=None,
        filepath=None,
        tolerance=None,
        angularTolerance=None,
    ):
        asyncio.run(
            self.render_stl_async(project, filepath, tolerance, angularTolerance)
        )

    async def render_3mf_async(
        self,
        project=None,
        filepath=None,
        tolerance=None,
        angularTolerance=None,
    ):
        with pc_logging.Action("Render3MF", self.project_name, self.name):
            threemf_opts, filepath = self.render_getopts(
                "3mf", ".3mf", project, filepath
            )

            if tolerance is None:
                if (
                    "tolerance" in threemf_opts
                    and not threemf_opts["tolerance"] is None
                ):
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

            cq_obj = await self.get_cadquery()

            def do_render_3mf():
                nonlocal cq_obj, project, filepath, tolerance, angularTolerance
                if not project is None:
                    project.ctx.ensure_dirs_for_file(filepath)
                cq.exporters.export(
                    cq_obj,
                    filepath,
                    tolerance=tolerance,
                    angularTolerance=angularTolerance,
                )

            await pc_thread.run(do_render_3mf)

    def render_3mf(
        self,
        project=None,
        filepath=None,
        tolerance=None,
        angularTolerance=None,
    ):
        asyncio.run(
            self.render_3mf_async(project, filepath, tolerance, angularTolerance)
        )

    async def render_threejs_async(
        self,
        project=None,
        filepath=None,
        tolerance=None,
        angularTolerance=None,
    ):
        with pc_logging.Action("RenderThreeJS", self.project_name, self.name):
            threejs_opts, filepath = self.render_getopts(
                "threejs", ".json", project, filepath
            )

            if tolerance is None:
                if (
                    "tolerance" in threejs_opts
                    and not threejs_opts["tolerance"] is None
                ):
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

            cq_obj = await self.get_cadquery()

            def do_render_threejs():
                nonlocal cq_obj, project, filepath, tolerance, angularTolerance
                if not project is None:
                    project.ctx.ensure_dirs_for_file(filepath)
                cq.exporters.export(
                    cq_obj,
                    filepath,
                    tolerance=tolerance,
                    angularTolerance=angularTolerance,
                    exportType=cq.exporters.ExportTypes.TJS,
                )

            await pc_thread.run(do_render_threejs)

    def render_threejs(
        self,
        project=None,
        filepath=None,
        tolerance=None,
        angularTolerance=None,
    ):
        asyncio.run(
            self.render_threejs_async(project, filepath, tolerance, angularTolerance)
        )

    async def render_obj_async(
        self,
        project=None,
        filepath=None,
        tolerance=None,
        angularTolerance=None,
    ):
        with pc_logging.Action("RenderOBJ", self.project_name, self.name):
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

            cq_obj = await self.get_cadquery()

            def do_render_obj():
                nonlocal cq_obj, project, filepath, tolerance, angularTolerance
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
                    pc_logging.error("Exception while exporting to " + filepath)

            await pc_thread.run(do_render_obj)

    def render_obj(
        self,
        project=None,
        filepath=None,
        tolerance=None,
        angularTolerance=None,
    ):
        asyncio.run(
            self.render_obj_async(project, filepath, tolerance, angularTolerance)
        )

    async def render_txt_async(self, project=None, filepath=None):
        with pc_logging.Action("RenderTXT", self.project_name, self.name):
            if filepath is None:
                filepath = self.path + "/bom.txt"

            if not project is None:
                project.ctx.ensure_dirs_for_file(filepath)
            file = open(filepath, "w+")
            file.write("BoM:\n")
            await self._render_txt_real(file)
            file.close()

    def render_txt(self, project=None, filepath=None):
        asyncio.run(self.render_txt_async(project, filepath))

    async def render_markdown_async(self, project=None, filepath=None):
        with pc_logging.Action("RenderMD", self.project_name, self.name):
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

    def render_markdown(self, project=None, filepath=None):
        asyncio.run(self.render_markdown_async(project, filepath))
