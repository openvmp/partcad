#
# OpenVMP, 2024
#
# Author: Roman Kuzmenko
# Created: 2024-02-04
#
# Licensed under Apache License, Version 2.0.

import logging
from logging import DEBUG, INFO, WARN, WARNING, ERROR, CRITICAL
import threading
import time

setLevel = lambda *args, **kwargs: logging.getLogger("partcad").setLevel(
    *args, **kwargs
)
log = lambda *args, **kwargs: logging.getLogger("partcad").log(*args, **kwargs)
debug = lambda *args, **kwargs: logging.getLogger("partcad").debug(
    *args, **kwargs
)
info = lambda *args, **kwargs: logging.getLogger("partcad").info(
    *args, **kwargs
)
warn = lambda *args, **kwargs: logging.getLogger("partcad").warn(
    *args, **kwargs
)
warning = lambda *args, **kwargs: logging.getLogger("partcad").warning(
    *args, **kwargs
)
error = lambda *args, **kwargs: logging.getLogger("partcad").error(
    *args, **kwargs
)
critical = lambda *args, **kwargs: logging.getLogger("partcad").critical(
    *args, **kwargs
)


# Some pytest versions/configurations/plugins mess with the exception method
# so lambdas don't work
def exception(
    *args,
):
    logging.getLogger("partcad").exception(*args)


def default_process_start(self_ops, op: str, package: str, item: str = None):
    if item is None:
        info("Starting process: %s: %s" % (op, package))
    else:
        info("Starting process: %s: %s: %s" % (op, package, item))


def default_process_end(self_ops, op: str, package: str, item: str = None):
    _ignore = True


def default_action_start(self_ops, op: str, package: str, item: str = None):
    if item is None:
        info("Starting action: %s: %s" % (op, package))
    else:
        info("Starting action: %s: %s: %s" % (op, package, item))


def default_action_end(self_ops, op: str, package: str, item: str = None):
    _ignore = True


# Dependency injection point for logging plugins
class Ops:
    process_start = default_process_start
    process_end = default_process_end
    action_start = default_action_start
    action_end = default_action_end


ops = Ops()


# Only one process at a time, no recursion
process_lock = threading.Lock()


# classes to be used with "with()" for blocks to be logged
class Process(object):
    def __init__(self, op: str, package: str, item: str = None):
        self.op = op
        self.package = package
        self.item = item
        self.succeeded = False
        self.start = 0.0

    async def __aenter__(self):
        self.__enter__()

    def __enter__(self):
        global process_lock

        if process_lock.acquire():
            self.start = time.time()
            ops.process_start(self.op, self.package, self.item)
            self.succeeded = True
        else:
            error("Nested process is detected. Status reporting is invalid.")
            self.succeeded = False

    async def __aexit__(self, *args):
        self.__exit__(*args)

    def __exit__(self, *_args):
        global process_lock
        global info

        if self.succeeded:
            process_lock.release()
            ops.process_end(self.op, self.package, self.item)

            delta = time.time() - self.start
            if self.item is None:
                info("DONE: %s: %s: %.2fs" % (self.op, self.package, delta))
            else:
                info(
                    "DONE: %s: %s: %s: %.2fs"
                    % (self.op, self.package, self.item, delta)
                )


class Action(object):
    def __init__(self, op: str, package: str, item: str = None):
        self.op = op
        self.package = package
        self.item = item

    async def __aenter__(self):
        self.__enter__()

    def __enter__(self):
        ops.action_start(self.op, self.package, self.item)

    async def __aexit__(self, *args):
        self.__exit__(*args)

    def __exit__(self, *_args):
        ops.action_end(self.op, self.package, self.item)
