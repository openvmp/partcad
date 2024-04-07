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
import base64
import os
import pathlib
import pickle
import shutil
import sys
import tempfile

from .render import *
from .plugins import *
from .shape_config import ShapeConfiguration
from . import logging as pc_logging
from . import sync_threads as pc_thread
from . import wrapper

sys.path.append(os.path.join(os.path.dirname(__file__), "wrappers"))
from cq_serialize import register as register_cq_helper


class Shape(ShapeConfiguration):
    name: str
    desc: str
    svg_path: str
    svg_url: str
    # shape: None | b3d.TopoDS_Shape | OCP.TopoDS.TopoDS_Solid

    def __init__(self, config):
        super().__init__(config)
        self.lock = asyncio.Lock()
        self.shape = None
        self.compound = None

        # Leave the svg path empty to get it created on demand
        self.svg_lock = asyncio.Lock()
        self.svg_path = None
        self.svg_url = None

    async def get_wrapped(self):
        shape = await self.get_shape()
        if "offset" in self.config:
            b3d_solid = b3d.Solid.make_box(1, 1, 1)
            b3d_solid.wrapped = shape
            b3d_solid.relocate(b3d.Location(*self.config["offset"]))
            shape = b3d_solid.wrapped
        if "scale" in self.config:
            b3d_solid = b3d.Solid.make_box(1, 1, 1)
            b3d_solid.wrapped = shape
            b3d_solid = b3d_solid.scale(self.config["scale"])
            shape = b3d_solid.wrapped
        return shape

    async def get_cadquery(self) -> cq.Shape:
        cq_solid = cq.Solid.makeBox(1, 1, 1)
        cq_solid.wrapped = await self.get_wrapped()
        return cq_solid

    async def get_build123d(self) -> b3d.Solid:
        b3d_solid = b3d.Solid.make_box(1, 1, 1)
        b3d_solid.wrapped = await self.get_wrapped()
        return b3d_solid

    def regenerate(self):
        if hasattr(self, "generate"):
            # Invalidate the shape
            # async with self.lock:
            self.shape = None

            # # Truncate the source code file
            # # This will trigger the regeneration of the file on instantiation
            # p = pathlib.Path(self.path)
            # p.unlink(missing_ok=True)
            # p.touch()
            self.generate()
        else:
            pc_logging.error("No generation function found")

    async def show_async(self, show_object=None):
        with pc_logging.Action("Show", self.project_name, self.name):
            try:
                shape = await self.get_wrapped()
            except Exception as e:
                pc_logging.error(e)

            if shape is not None:
                if show_object is None:
                    import importlib

                    ocp_vscode = importlib.import_module("ocp_vscode")
                    if ocp_vscode is None:
                        pc_logging.warning(
                            'Failed to load "ocp_vscode". Giving up on connection to VS Code.'
                        )
                    else:
                        try:
                            # ocp_vscode.config.status()
                            pc_logging.info(
                                'Visualizing in "OCP CAD Viewer"...'
                            )
                            # pc_logging.debug(self.shape)
                            ocp_vscode.show(
                                shape,
                                progress=None,
                                # TODO(clairbee): make showing (and the connection
                                # to ocp_vscode) a part of the context, and memorize
                                # which part was displayed last. Keep the camera
                                # if the part has not changed.
                                # reset_camera=ocp_vscode.Camera.KEEP,
                            )
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

    async def render_svg_somewhere(
        self,
        ctx,
        project=None,
        filepath=None,
        line_weight=None,
        viewport_origin=None,
    ):
        """Renders an SVG file somewhere and ignore the project settings"""
        if filepath is None:
            filepath = tempfile.mktemp(".svg")

        obj = await self.get_wrapped()
        if obj is None:
            # pc_logging.error("The shape failed to instantiate")
            self.svg_path = None
            return

        svg_opts, _ = self.render_getopts("svg", ".svg", project, filepath)

        if line_weight is None:
            if "lineWeight" in svg_opts and not svg_opts["lineWeight"] is None:
                line_weight = svg_opts["lineWeight"]
            else:
                line_weight = 1.0

        if viewport_origin is None:
            if (
                "viewportOrigin" in svg_opts
                and not svg_opts["viewportOrigin"] is None
            ):
                viewport_origin = svg_opts["viewportOrigin"]
            else:
                viewport_origin = [100, -100, 100]

        wrapper_path = wrapper.get("render_svg.py")
        request = {
            "wrapped": obj,
            "line_weight": line_weight,
            "viewport_origin": viewport_origin,
        }
        register_cq_helper()
        picklestring = pickle.dumps(request)
        request_serialized = base64.b64encode(picklestring).decode()

        runtime = ctx.get_python_runtime(python_runtime="none")
        await runtime.ensure("build123d")
        response_serialized, errors = await runtime.run(
            [
                wrapper_path,
                os.path.abspath(filepath),
            ],
            request_serialized,
        )
        sys.stderr.write(errors)

        response = base64.b64decode(response_serialized)
        result = pickle.loads(response)
        if not result["success"]:
            pc_logging.error(
                "RenderSVG failed: %s: %s" % (self.name, result["exception"])
            )
        if "exception" in result and not result["exception"] is None:
            pc_logging.exception(
                "RenderSVG exception: %s" % result["exception"]
            )

        self.svg_path = filepath

    async def _get_svg_path(self, ctx, project):
        async with self.svg_lock:
            if self.svg_path is None:
                await self.render_svg_somewhere(ctx=ctx, project=project)
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

        if (
            "render" in self.config
            and not self.config["render"] is None
            and kind in self.config["render"]
            and not self.config["render"][kind] is None
        ):
            shape_opts = self.config["render"][kind]
            if isinstance(shape_opts, str):
                shape_opts = {"prefix": shape_opts}
            opts = render_cfg_merge(opts, shape_opts)

        # Using the project's config defaults if any
        if filepath is None:
            if "path" in opts and not opts["path"] is None:
                filepath = opts["path"]
            elif "prefix" in opts and not opts["prefix"] is None:
                filepath = opts["prefix"]
            else:
                filepath = "."

            # Check if the format specific section of the config (e.g. "png")
            # provides a relative path and there is output dir in cmd line or
            # the generic section of rendering options in the config.
            if not os.path.isabs(filepath):
                if "output_dir" in render_opts:
                    filepath = os.path.join(render_opts["output_dir"], filepath)
                elif not project is None:
                    filepath = os.path.join(project.config_dir, filepath)

            if os.path.isdir(filepath):
                filepath = os.path.join(filepath, self.name + extension)

        pc_logging.debug("Rendering: %s" % filepath)

        return opts, filepath

    async def render_svg_async(
        self,
        ctx,
        project=None,
        filepath=None,
    ):
        with pc_logging.Action("RenderSVG", self.project_name, self.name):
            _, filepath = self.render_getopts("svg", ".svg", project, filepath)

            # This creates a temporary file, but it allows to reuse the file
            # with other consumers of self._get_svg_path()
            svg_path = await self._get_svg_path(ctx=ctx, project=project)
            if not svg_path is None and svg_path != filepath:
                if os.path.exists(svg_path):
                    shutil.copyfile(svg_path, filepath)
                else:
                    pc_logging.error("SVG file was not created by the wrapper")

    def render_svg(
        self,
        ctx,
        project=None,
        filepath=None,
    ):
        asyncio.run(self.render_svg_async(ctx, project, filepath))

    async def render_png_async(
        self,
        ctx,
        project=None,
        filepath=None,
        width=None,
        height=None,
    ):
        with pc_logging.Action("RenderPNG", self.project_name, self.name):
            if not plugins.export_png.is_supported():
                pc_logging.error("Export to PNG is not supported")
                return

            png_opts, filepath = self.render_getopts(
                "png", ".png", project, filepath
            )

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
            svg_path = await self._get_svg_path(ctx=ctx, project=project)

            def do_render_png():
                nonlocal project, svg_path, width, height, filepath
                plugins.export_png.export(
                    project, svg_path, width, height, filepath
                )

            await pc_thread.run(do_render_png)

    def render_png(
        self,
        ctx,
        project=None,
        filepath=None,
        width=None,
        height=None,
    ):
        asyncio.run(
            self.render_png_async(ctx, project, filepath, width, height)
        )

    async def render_step_async(
        self,
        ctx,
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
        ctx,
        project=None,
        filepath=None,
    ):
        asyncio.run(self.render_step_async(ctx, project, filepath))

    async def render_stl_async(
        self,
        ctx,
        project=None,
        filepath=None,
        tolerance=None,
        angularTolerance=None,
    ):
        with pc_logging.Action("RenderSTL", self.project_name, self.name):
            stl_opts, filepath = self.render_getopts(
                "stl", ".stl", project, filepath
            )

            if tolerance is None:
                if (
                    "tolerance" in stl_opts
                    and not stl_opts["tolerance"] is None
                ):
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
        ctx,
        project=None,
        filepath=None,
        tolerance=None,
        angularTolerance=None,
    ):
        asyncio.run(
            self.render_stl_async(
                ctx, project, filepath, tolerance, angularTolerance
            )
        )

    async def render_3mf_async(
        self,
        ctx,
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
        ctx,
        project=None,
        filepath=None,
        tolerance=None,
        angularTolerance=None,
    ):
        asyncio.run(
            self.render_3mf_async(
                ctx, project, filepath, tolerance, angularTolerance
            )
        )

    async def render_threejs_async(
        self,
        ctx,
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
        ctx,
        project=None,
        filepath=None,
        tolerance=None,
        angularTolerance=None,
    ):
        asyncio.run(
            self.render_threejs_async(
                ctx, project, filepath, tolerance, angularTolerance
            )
        )

    async def render_obj_async(
        self,
        ctx,
        project=None,
        filepath=None,
        tolerance=None,
        angularTolerance=None,
    ):
        with pc_logging.Action("RenderOBJ", self.project_name, self.name):
            obj_opts, filepath = self.render_getopts(
                "obj", ".obj", project, filepath
            )

            if tolerance is None:
                if (
                    "tolerance" in obj_opts
                    and not obj_opts["tolerance"] is None
                ):
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

            obj = await self.get_wrapped()
            wrapper_path = wrapper.get("render_obj.py")
            request = {
                "wrapped": obj,
                "tolerance": tolerance,
                "angularTolerance": angularTolerance,
            }
            register_cq_helper()
            picklestring = pickle.dumps(request)
            request_serialized = base64.b64encode(picklestring).decode()

            runtime = ctx.get_python_runtime(python_runtime="none")
            await runtime.ensure("cadquery")
            response_serialized, errors = await runtime.run(
                [
                    wrapper_path,
                    os.path.abspath(filepath),
                ],
                request_serialized,
            )
            sys.stderr.write(errors)

            response = base64.b64decode(response_serialized)
            result = pickle.loads(response)

            if not result["success"]:
                pc_logging.error(
                    "RenderOBJ faled: %s: %s" % (self.name, result["exception"])
                )
            if "exception" in result and not result["exception"] is None:
                pc_logging.exception(result["exception"])

    def render_obj(
        self,
        ctx,
        project=None,
        filepath=None,
        tolerance=None,
        angularTolerance=None,
    ):
        asyncio.run(
            self.render_obj_async(
                ctx, project, filepath, tolerance, angularTolerance
            )
        )

    async def render_gltf_async(
        self,
        ctx,
        project=None,
        filepath=None,
        binary=None,
        tolerance=None,
        angularTolerance=None,
    ):
        with pc_logging.Action("RenderGLTF", self.project_name, self.name):
            gltf_opts, filepath = self.render_getopts(
                "gltf", ".json", project, filepath
            )

            if tolerance is None:
                if (
                    "tolerance" in gltf_opts
                    and not gltf_opts["tolerance"] is None
                ):
                    tolerance = gltf_opts["tolerance"]
                else:
                    tolerance = 0.1

            if angularTolerance is None:
                if (
                    "angularTolerance" in gltf_opts
                    and not gltf_opts["angularTolerance"] is None
                ):
                    angularTolerance = gltf_opts["angularTolerance"]
                else:
                    angularTolerance = 0.1

            if binary is None:
                if "binary" in gltf_opts and not gltf_opts["binary"] is None:
                    binary = gltf_opts["binary"]
                else:
                    binary = False

            b3d_obj = await self.get_build123d()

            def do_render_gltf():
                nonlocal b3d_obj, project, filepath, tolerance, angularTolerance
                b3d.export_gltf(
                    b3d_obj,
                    filepath,
                    binary=binary,
                    linear_deflection=tolerance,
                    angular_deflection=angularTolerance,
                )

            await pc_thread.run(do_render_gltf)

    def render_gltf(
        self,
        ctx,
        project=None,
        filepath=None,
        tolerance=None,
        angularTolerance=None,
    ):
        asyncio.run(
            self.render_gltf_async(
                ctx, project, filepath, tolerance, angularTolerance
            )
        )

    async def render_txt_async(self, ctx, project=None, filepath=None):
        with pc_logging.Action("RenderTXT", self.project_name, self.name):
            if filepath is None:
                filepath = self.path + "/bom.txt"

            if not project is None:
                project.ctx.ensure_dirs_for_file(filepath)
            file = open(filepath, "w+")
            file.write("BoM:\n")
            await self._render_txt_real(file)
            file.close()

    def render_txt(self, ctx, project=None, filepath=None):
        asyncio.run(self.render_txt_async(ctx, project, filepath))

    async def render_markdown_async(self, ctx, project=None, filepath=None):
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

    def render_markdown(self, ctx, project=None, filepath=None):
        asyncio.run(self.render_markdown_async(ctx, project, filepath))

    async def get_summary_async(self, project=None):
        if "summary" in self.config and not self.config["summary"] is None:
            return self.config["summary"]
        return None

    def get_summary(self, project=None):
        asyncio.run(self.get_summary_async(project))
