#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-30
#
# Licensed under Apache License, Version 2.0.

import asyncio
import hashlib
import os
import pathlib
import subprocess
import sys
import threading

from . import runtime
from . import logging as pc_logging


class PythonRuntime(runtime.Runtime):
    def __init__(self, ctx, sandbox, version=None):
        if version is None:
            version = "%d.%d" % (sys.version_info.major, sys.version_info.minor)
        super().__init__(ctx, "python-" + sandbox + "-" + version)
        self.version = version

        # Runtimes are meant to be executed from dedicated threads, outside of
        # the asyncio event loop. So a threading lock is appropriate here.
        self.lock = threading.RLock()

    async def run(self, cmd, stdin=""):
        pc_logging.debug("Running: %s", cmd)
        # p = subprocess.Popen(
        p = await asyncio.create_subprocess_exec(
            # cmd,
            cmd[0],
            *cmd[1:],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            # TODO(clairbee): creationflags=subprocess.CREATE_NO_WINDOW,
        )
        stdout, stderr = await p.communicate(
            input=stdin.encode(),
            # TODO(clairbee): add timeout
        )

        stdout = stdout.decode()
        stderr = stderr.decode()

        # TODO(clairbee): remove the below when a better troubleshooting mechanism is introduced
        # f = open("/tmp/log", "w")
        # f.write("Completed: %s\n" % cmd)
        # f.write(" stdin: %s\n" % stdin)
        # f.write(" stderr: %s\n" % stderr)
        # f.write(" stdout: %s\n" % stdout)
        # f.close()

        return stdout, stderr

    async def ensure(self, python_package):
        # TODO(clairbee): add support for versioned packages
        # TODO(clairbee): expire the guard file after a certain time

        guard_path = os.path.join(
            self.path, ".partcad.installed." + python_package
        )
        with self.lock:
            if not os.path.exists(guard_path):
                with pc_logging.Action("PipInst", self.version, python_package):
                    await self.run(
                        ["-m", "pip", "install", "-U", python_package]
                    )
                pathlib.Path(guard_path).touch()

    async def prepare_for_package(self, project):
        # TODO(clairbee): expire the guard file after a certain time

        # Check if this project has python requirements
        requirements_path = os.path.join(project.path, "requirements.txt")
        if os.path.exists(requirements_path):
            # See if it was already prepared once
            project_hash = hashlib.sha256(project.path.encode()).hexdigest()
            flag_filename = ".partcad.project." + project_hash
            flag_path = os.path.join(self.path, flag_filename)
            with self.lock:
                if not os.path.exists(flag_path) or os.path.getmtime(
                    requirements_path
                ) > os.path.getmtime(flag_path):
                    # Install requirements and remember when we did that
                    with pc_logging.Action(
                        "PipReqs", self.version, project.name
                    ):
                        await self.run(
                            [
                                "-m",
                                "pip",
                                "install",
                                "-r",
                                requirements_path,
                            ]
                        )
                    pathlib.Path(flag_path).touch()
