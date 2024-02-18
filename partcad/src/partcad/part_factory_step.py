#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-08-19
#
# Licensed under Apache License, Version 2.0.
#

import cadquery as cq

import base64
import os
import pickle
import sys
import threading
import time

from . import logging as pc_logging
from . import wrapper
from . import part_factory_file as pff


class PartFactoryStep(pff.PartFactoryFile):
    # How many STEP files should be loaded directly simultaneously (without
    # launching a subprocess), no matter the file size.
    MIN_SIMPLE_INFLIGHT = 1

    # How big of a STEP file is needed to consider launching a sub-process.
    MIN_SUBPROCESS_FILE_SIZE = 64 * 1024

    # lock is used to protect changes to the static class members
    lock = threading.Lock()
    # How many of the current instances are in which mode?
    count_inflight_simple = 0
    count_inflight_subprocess = 0

    def __init__(self, ctx, project, part_config):
        with pc_logging.Action("InitSTEP", project.name, part_config["name"]):
            super().__init__(ctx, project, part_config, extension=".step")
            # Complement the config object here if necessary
            self._create(part_config)

            self.runtime = None

    def instantiate(self, part):
        with pc_logging.Action("STEP", part.project_name, part.name):
            do_subprocess = False

            file_size = os.path.getsize(self.path)

            with PartFactoryStep.lock:
                if (
                    PartFactoryStep.count_inflight_simple
                    < PartFactoryStep.MIN_SIMPLE_INFLIGHT
                    or file_size < PartFactoryStep.MIN_SUBPROCESS_FILE_SIZE
                ):
                    PartFactoryStep.count_inflight_simple += 1
                else:
                    do_subprocess = True
                    PartFactoryStep.count_inflight_subprocess += 1
                    if self.runtime == None:
                        self.runtime = self.ctx.get_python_runtime(
                            self.project.python_version
                        )

            if do_subprocess:
                wrapper_path = wrapper.get("step.py")

                request = {"build_parameters": {}}
                picklestring = pickle.dumps(request)
                request_serialized = base64.b64encode(picklestring).decode()

                self.runtime.ensure("cadquery")
                response_serialized, errors = self.runtime.run(
                    [
                        wrapper_path,
                        os.path.abspath(self.path),
                        os.path.abspath(self.project.config_dir),
                    ],
                    request_serialized,
                )
                sys.stderr.write(errors)

                response = base64.b64decode(response_serialized)
                result = pickle.loads(response)

                if not result["success"]:
                    pc_logging.error(result["exception"])
                    raise Exception(result["exception"])
                shape = result["shape"]
            else:
                # Thanks for CadQuery deficiencies in handling of GIL,
                # as soon as 'importStep()' is called, all of other Python
                # threads are going to be frozen, so we need to give other
                # threads an opportunity to spawn processes to stay busy during
                # the 'importStep()' call.
                time.sleep(0.0001)
                time.sleep(0.0001)
                time.sleep(0.0001)
                time.sleep(0.0001)
                time.sleep(0.0001)
                time.sleep(0.0001)
                time.sleep(0.0001)
                time.sleep(0.0001)
                time.sleep(0.0001)
                time.sleep(0.0001)
                time.sleep(0.0001)
                time.sleep(0.0001)
                time.sleep(0.0001)
                time.sleep(0.0001)
                time.sleep(0.0001)
                time.sleep(0.0001)
                time.sleep(0.0001)
                time.sleep(0.0001)
                time.sleep(0.0001)
                time.sleep(0.0001)
                # TODO(clairbee): remove sleep calls when GIL is fixed in CQ

                shape = cq.importers.importStep(self.path).val().wrapped

            with PartFactoryStep.lock:
                if do_subprocess:
                    PartFactoryStep.count_inflight_subprocess -= 1
                else:
                    PartFactoryStep.count_inflight_simple -= 1

            self.ctx.stats_parts_instantiated += 1

            return shape
