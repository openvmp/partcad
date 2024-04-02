#
# OpenVMP, 2024
#
# Author: Roman Kuzmenko
# Created: 2024-02-04
#
# Licensed under Apache License, Version 2.0.

import asyncio
import atexit
import logging
from logging.handlers import QueueHandler, QueueListener
import queue
import sys
import time
from typing import Any
import threading

from .logging import ops, error

COLOR_DEBUG = "\033[94m"
COLOR_INFO = "\033[92m\033[1m"
COLOR_WARN = "\033[93m"
COLOR_ERROR = "\033[91m"
COLOR_CRIT = "\033[91m\033[1m"
COLOR_NONE = "\033[0m"

COLOR_ACTION = "\033[1m"

WRAP = "\033[?7h"
NO_WRAP = "\033[?7l"


def ansi_process_start(op: str, package: str, item: str = None):
    logging.getLogger("partcad").critical(
        "process_start: %s: %s: %s" % (op, package, item),
        extra={
            "pc_event": "process_start",
            "op": op,
            "package": package,
            "item": item,
        },
    )


def ansi_process_end(op: str, package: str, item: str = None):
    logging.getLogger("partcad").critical(
        "process_end: %s: %s: %s" % (op, package, item),
        extra={
            "pc_event": "process_end",
            "op": op,
            "package": package,
            "item": item,
        },
    )


def ansi_action_start(op: str, package: str, item: str = None):
    logging.getLogger("partcad").critical(
        "action_start: %s: %s: %s" % (op, package, item),
        extra={
            "pc_event": "action_start",
            "op": op,
            "package": package,
            "item": item,
        },
    )


def ansi_action_end(op: str, package: str, item: str = None):
    logging.getLogger("partcad").critical(
        "action_end: %s: %s: %s" % (op, package, item),
        extra={
            "pc_event": "action_end",
            "op": op,
            "package": package,
            "item": item,
        },
    )


class AnsiTerminalProgressHandler(logging.Handler):
    MAX_LINES = 8

    def __init__(self, stream=sys.stdout) -> None:
        super().__init__()
        self.thread_lock = threading.Lock()
        if not stream is None:
            self.stream = stream
        else:
            self.stream = sys.stdout

        self.thread = None

        self.process = None
        self.process_target = None
        self.process_start = None
        self.footer_size = 0

        self.actions = {}
        self.actions_running = 0
        self.actions_total = 0

        self.last_output = 0.0

    def clear_footer(self):
        return "\u001b[1A\u001b[2K" * self.footer_size

    def run_thread(self):
        while not self.process is None:
            time.sleep(0.25)
            if time.time() - self.last_output > 0.5:
                self.emit(None)

    def emit(self, record):
        now = time.time()

        # output accumulates the string that will be emitted before 'return'
        output = ""

        # protect the status data store in 'self' from other threads
        self.thread_lock.acquire()

        if not record is None:
            ignore_message = False
            if hasattr(record, "pc_event"):
                if record.pc_event == "process_start":
                    self.process = record.op
                    self.process_target = record.package
                    if record.item is not None:
                        self.process_target += ":" + record.item
                    self.process_start = time.time()
                    self.actions_total = 0

                    if not self.thread is None:
                        self.thread_lock.release()
                        raise Exception("nested processes")
                    self.thread = threading.Thread(
                        target=self.run_thread,
                        name="ansi-terminal-update-" + str(now),
                    )
                    self.thread_lock.release()
                    self.thread.start()
                    return
                elif record.pc_event == "process_end":
                    self.process = None  # This also signals the thread to stop
                    output += self.clear_footer()
                    self.footer_size = 0

                    self.last_output = 0.0
                    th = self.thread
                    self.thread = None
                    self.thread_lock.release()

                    th.join()

                    if len(output) > 0:
                        self.stream.write(output)
                        self.stream.flush()
                    return

                elif record.pc_event == "action_start":
                    action = {"op": record.op}
                    target = record.package
                    if record.item is not None:
                        target += ":" + record.item
                    action["target"] = target
                    action["start"] = time.time()
                    self.actions[record.op + "-" + target] = action

                    self.actions_running += 1
                    self.actions_total += 1
                elif record.pc_event == "action_end":
                    target = record.package
                    if record.item is not None:
                        target += ":" + record.item
                    action_key = record.op + "-" + target
                    if action_key in self.actions:
                        del self.actions[record.op + "-" + target]
                    else:
                        error(
                            "action_key not found: %s: among %s"
                            % (action_key, str(self.actions.keys()))
                        )

                    self.actions_running -= 1
                ignore_message = True

        output += self.clear_footer()

        if not record is None:
            if not ignore_message:
                if record.levelno == logging.DEBUG:
                    output += COLOR_DEBUG + "DEBUG:" + COLOR_NONE + " "
                elif record.levelno == logging.INFO:
                    output += COLOR_INFO + "INFO: " + COLOR_NONE + " "
                elif record.levelno == logging.WARN:
                    output += COLOR_WARN + "WARN:" + COLOR_NONE + " "
                elif record.levelno == logging.ERROR:
                    output += COLOR_ERROR + "ERROR:" + COLOR_NONE + " "
                elif record.levelno == logging.CRITICAL:
                    output += COLOR_CRIT + "CRIT:" + COLOR_NONE + " "

                msg = self.format(record)
                output += "%s\n" % msg

        if not self.process is None:
            seconds = int(now - self.process_start)

            output += NO_WRAP
            output += "%s[ %d / %d ]%s %s%s%s %s; %ds\n" % (
                COLOR_INFO,
                self.actions_running,
                self.actions_total,
                COLOR_NONE,
                COLOR_ACTION,
                self.process,
                COLOR_NONE,
                self.process_target,
                seconds,
            )
            self.footer_size = 1

            sorted_actions = sorted(
                self.actions.values(), key=lambda a: a["start"]
            )
            sorted_actions = sorted_actions[: self.MAX_LINES]
            for action in sorted_actions:
                output += "%s\t[%s]%s %s [%ds]\n" % (
                    COLOR_ACTION,
                    action["op"],
                    COLOR_NONE,
                    action["target"],
                    now - action["start"],
                )
                self.footer_size += 1
            output += WRAP
        else:
            self.footer_size = 0

        self.last_output = now
        self.thread_lock.release()
        if len(output) > 0:
            self.stream.write(output)
            self.stream.flush()

        return


listener = None
queue_handler: AnsiTerminalProgressHandler = None


def fini():
    global listener
    if not listener is None:
        atexit.unregister(fini)
        listener.stop()
        listener = None


def init(stream=None):
    global listener
    global ops

    log_queue = queue.Queue(-1)
    queue_handler = QueueHandler(log_queue)
    output_handler = AnsiTerminalProgressHandler(stream=stream)

    logger = logging.getLogger("partcad")
    handlers = logger.handlers
    for handler in handlers:
        logger.removeHandler(handler)
    logger.addHandler(queue_handler)

    listener = QueueListener(log_queue, output_handler)
    listener.start()
    atexit.register(fini)

    ops.process_start = ansi_process_start
    ops.process_end = ansi_process_end
    ops.action_start = ansi_action_start
    ops.action_end = ansi_action_end
