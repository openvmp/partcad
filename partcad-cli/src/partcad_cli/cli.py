#!/usr/bin/env python
#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-22
#
# Licensed under Apache License, Version 2.0.
#

import argparse
import logging
import sys

import partcad as pc
import partcad.logging as pc_logging
from partcad.user_config import user_config

from .cli_add import *
from .cli_init import *
from .cli_info import *
from .cli_install import *
from .cli_list import *
from .cli_render import *
from .cli_inspect import *
from .cli_status import *
from .cli_supply_find import *
from .cli_supply_caps import *
from .cli_supply_order import *
from .cli_supply_quote import *


# Initialize plugins that are not enabled by default
pc.plugins.export_png = pc.PluginExportPngReportlab()


def main():
    parser = argparse.ArgumentParser(
        description="PartCAD command line tool",
    )
    parser.add_argument(
        "-v",
        help="Increase the level of verbosity",
        dest="verbosity",
        action="count",
        default=0,
    )
    parser.add_argument(
        "-q",
        help="Decrease the level of verbosity",
        dest="quiet",
        action="count",
        default=0,
    )
    parser.add_argument(
        "--no-ansi",
        help="Plain logging output. Do not use colors or animations.",
        dest="no_ansi",
        action="store_true",
    )
    parser.add_argument(
        "-p",
        help="Package path (a YAML file or a directory with 'partcad.yaml')",
        type=str,
        default=None,
        dest="config_path",
    )
    # TODO(clairbee): add a config option to change logging mechanism and level

    # Top level commands
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser(
        "version",
        help="Print PartCAD version and exit",
    )
    cli_help_add(subparsers)
    cli_help_init(subparsers)
    cli_help_info(subparsers)
    cli_help_install(subparsers)
    cli_help_list(subparsers)
    cli_help_render(subparsers)
    cli_help_inspect(subparsers)
    cli_help_status(subparsers)

    # Supply subcommands
    parser_supply = subparsers.add_parser(
        "supply",
        help="Supplier related commands",
    )
    supply_subparsers = parser_supply.add_subparsers(
        dest="supply_command",
        required=True,
    )
    cli_help_supply_find(supply_subparsers)
    cli_help_supply_caps(supply_subparsers)
    cli_help_supply_quote(supply_subparsers)
    cli_help_supply_order(supply_subparsers)

    args = parser.parse_args()

    # Configure logging
    if not args.no_ansi:
        pc.logging_ansi_terminal_init()
    else:
        logging.basicConfig()

    if args.quiet > 0:
        pc.logging.setLevel(logging.CRITICAL + 1)
    else:
        if args.verbosity > 0:
            pc.logging.setLevel(logging.DEBUG)
        else:
            pc.logging.setLevel(logging.INFO)

    try:
        # First, handle the commands that don't require a context or initialize it
        # in their own way
        if args.command == "init":
            cli_init(args)
            return
        elif args.command == "status":
            cli_status(args)
            return
        elif args.command == "version":
            pc_logging.info("PartCAD version: %s" % pc.__version__)
            return

        if args.command == "install" or args.command == "update":
            user_config.force_update = True

        # Initialize the context
        if not args.config_path is None:
            ctx = pc.init(args.config_path)
        else:
            ctx = pc.init()

        # Handle the command
        if args.command == "add":
            with pc_logging.Process("Add", "this"):
                cli_add(args, ctx)

        elif args.command == "add-part":
            with pc_logging.Process("AddPart", "this"):
                cli_add_part(args, ctx)

        elif args.command == "add-assembly":
            with pc_logging.Process("AddAssy", "this"):
                cli_add_assembly(args, ctx)

        elif args.command == "info":
            with pc_logging.Process("Info", "this"):
                cli_info(args, ctx)

        elif args.command == "install" or args.command == "update":
            with pc_logging.Process("Install", "this"):
                cli_install(args, ctx)

        elif args.command == "list":
            with pc_logging.Process("List", "this"):
                cli_list(args, ctx)

        elif args.command == "list-all":
            with pc_logging.Process("ListAll", "this"):
                cli_list_assemblies(args, ctx)
                cli_list_parts(args, ctx)

        elif args.command == "list-sketches":
            with pc_logging.Process("ListSketches", "this"):
                cli_list_sketches(args, ctx)

        elif args.command == "list-interfaces":
            with pc_logging.Process("ListInterfaces", "this"):
                cli_list_interfaces(args, ctx)

        elif args.command == "list-mates":
            with pc_logging.Process("ListMates", "this"):
                cli_list_mates(args, ctx)

        elif args.command == "list-parts":
            with pc_logging.Process("ListParts", "this"):
                cli_list_parts(args, ctx)

        elif args.command == "list-assemblies":
            with pc_logging.Process("ListAssy", "this"):
                cli_list_assemblies(args, ctx)

        elif args.command == "render":
            with pc_logging.Process("Render", "this"):
                cli_render(args, ctx)

        elif args.command == "inspect":
            with pc_logging.Process("inspect", "this"):
                cli_inspect(args, ctx)

        elif args.command == "supply":
            if args.supply_command == "find":
                with pc_logging.Process("SupplyFind", "this"):
                    cli_supply_find(args, ctx)
            elif args.supply_command == "caps":
                with pc_logging.Process("SupplyCaps", "this"):
                    cli_supply_caps(args, ctx)
            elif args.supply_command == "quote":
                with pc_logging.Process("SupplyQuote", "this"):
                    cli_supply_quote(args, ctx)
            elif args.supply_command == "order":
                with pc_logging.Process("SupplyOrder", "this"):
                    cli_supply_order(args, ctx)
            else:
                print("Unknown supply command.\n")
                parser.print_help()

        else:
            print("Unknown command.\n")
            parser.print_help()
    except:
        pc.logging.exception("PartCAD CLI exception")

    if not args.no_ansi:
        pc.logging_ansi_terminal_fini()
    if pc_logging.had_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
