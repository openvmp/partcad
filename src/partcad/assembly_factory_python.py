#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.
#

# import base64
import os

# import pickle
import sys

from . import assembly_factory as af

# from . import wrapper

from cadquery import cqgi

sys.path.append(os.path.join(os.path.dirname(__file__), "wrappers"))
from cq_serialize import (
    register as register_cq_helper,
)  # import this one for `pickle` to use


class AssemblyFactoryPython(af.AssemblyFactory):
    def __init__(self, ctx, project, assembly_config):
        super().__init__(ctx, project, assembly_config, extension=".py")
        # Complement the config object here if necessary
        self._create(assembly_config)

        cadquery_script = open(self.path, "r").read()

        # TODO(clairbee): this is a workaround to lack of support for 'atexit()'
        # in CQGI
        if "import partcad as pc" in cadquery_script:
            cadquery_script += "\npc.finalize_real()\n"
        # print(cadquery_script)

        script = cqgi.parse(cadquery_script)
        result = script.build(build_parameters={})
        if result.success:
            shape = result.first_result.shape
        else:
            shape = None

        if hasattr(shape, "val"):
            shape = shape.val()
        if hasattr(shape, "wrapped"):
            shape = shape.wrapped
        self.assembly.shape = shape

        # TODO(clairbee): Continue using CQGI (above) instead of a wrapper
        #                 process(below) until there an IPC mechanism to share
        #                 the PartCAD context.
        #
        # self.runtime = self.ctx.get_python_runtime(
        #     self.project.python_version,
        #     # python_runtime="none",
        # )
        # self.runtime.prepare_for_package(project)

        # wrapper_path = wrapper.get("partcad.py")

        # request = {"build_parameters": {}}
        # picklestring = pickle.dumps(request)
        # request_serialized = base64.b64encode(picklestring).decode()

        # self.runtime.ensure("partcad")
        # response_serialized, errors = self.runtime.run(
        #     [wrapper_path, self.path], request_serialized
        # )
        # sys.stderr.write(errors)

        # response = base64.b64decode(response_serialized)
        # result = pickle.loads(response)

        # if result["success"]:
        #     shape = result["shape"]
        #     self.part.shape = shape
        # else:
        #     print(result["exception"])

        self._save()
