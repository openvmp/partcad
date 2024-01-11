#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-23
#
# Licensed under Apache License, Version 2.0.
#

import logging
import partcad as pc


def cli_help_list(subparsers):
    parser_list = subparsers.add_parser(
        "list",
        help="List imported packages",
    )
    parser_list_all = subparsers.add_parser(
        "list-all",
        help="List available parts, assemblies and scenes",
    )
    parser_list_parts = subparsers.add_parser(
        "list-parts",
        help="List available parts",
    )
    parser_list_assemblies = subparsers.add_parser(
        "list-assemblies",
        help="List available assemblies",
    )

    parser_list_all.add_argument(
        "-r",
        help="Recursively process all imported packages",
        dest="recursive",
        action="store_true",
    )
    parser_list_parts.add_argument(
        "-r",
        help="Recursively process all imported packages",
        dest="recursive",
        action="store_true",
    )
    parser_list_assemblies.add_argument(
        "-r",
        help="Recursively process all imported packages",
        dest="recursive",
        action="store_true",
    )

    parser_list_all.add_argument(
        "-u",
        help="Only process objects used by the given assembly or scene.",
        dest="used_by",
        type=str,
        required=False,
    )
    parser_list_parts.add_argument(
        "-u",
        help="Only process objects used by the given assembly or scene.",
        dest="used_by",
        type=str,
        required=False,
    )
    parser_list_assemblies.add_argument(
        "-u",
        help="Only process objects used by the given assembly or scene.",
        dest="used_by",
        type=str,
        required=False,
    )


def cli_list(args):
    if not args.config_path is None:
        ctx = pc.init(args.config_path)
    else:
        ctx = pc.init()
    pkg_count = 0

    print()
    print("PartCAD dependencies:")
    for project_name in ctx.projects:
        if project_name == pc.THIS or project_name.startswith("partcad-"):
            continue

        project = ctx.projects[project_name]
        line = "\t%s" % project_name
        padding_size = 40 - len(project_name)
        if padding_size < 4:
            padding_size = 4
        line += " " * padding_size
        line += "%s" % project.desc
        print(line)
        pkg_count = pkg_count + 1

    if pkg_count < 1:
        print("\t<none>")


def cli_list_parts(args):
    if not args.config_path is None:
        ctx = pc.init(args.config_path)
    else:
        ctx = pc.init()
    part_count = 0
    part_kinds = 0

    if args.used_by is not None:
        print("Instantiating %s..." % args.used_by)
        pc.get_assembly(args.used_by)

    print()
    print("PartCAD parts:")
    for project_name in ctx.projects:
        if project_name != pc.THIS and not args.recursive:
            continue
        if project_name.startswith("partcad-"):
            continue
        project = ctx.projects[project_name]

        if args.used_by is None:
            if (
                "parts" in project.config_obj
                and project.config_obj["parts"] is not None
            ):
                part_names = project.config_obj["parts"].keys()
            else:
                part_names = []
        else:
            part_names = project.parts.keys()
        for part_name in part_names:
            line = "\t"
            if args.recursive:
                line += "%s" % project_name
                line += " " * (36 - len(project_name))
            line += "%s" % part_name
            if args.used_by is not None:
                part = project.parts[part_name]
                line += "(%d)" % part.count
                part_count = part_count + part.count
            line += " " * (36 - len(part_name))
            if (
                project.config_obj["parts"][part_name] is not None
                and "desc" in project.config_obj["parts"][part_name]
            ):
                line += "%s" % project.config_obj["parts"][part_name]["desc"]
            print(line)
            part_kinds = part_kinds + 1

    if part_kinds > 0:
        if args.used_by is None:
            print("Total: %d" % part_kinds)
        else:
            print("Total: %d parts of %d kinds" % (part_count, part_kinds))
    else:
        print("\t<none>")


def cli_list_assemblies(args):
    if not args.config_path is None:
        ctx = pc.init(args.config_path)
    else:
        ctx = pc.init()
    assy_count = 0
    assy_kinds = 0

    if args.used_by is not None:
        print("Instantiating %s..." % args.used_by)
        pc.get_assembly(args.used_by)

    print()
    print("PartCAD assemblies:")
    for project_name in ctx.projects:
        if project_name != pc.THIS and not args.recursive:
            continue
        if project_name.startswith("partcad-"):
            continue
        project = ctx.projects[project_name]

        if args.used_by is None:
            if (
                "assemblies" in project.config_obj
                and project.config_obj["assemblies"] is not None
            ):
                assy_names = project.config_obj["assemblies"].keys()
            else:
                assy_names = []
        else:
            assy_names = project.assemblies.keys()
        for assy_name in assy_names:
            line = "\t"
            if args.recursive:
                line += "%s" % project_name
                line += " " * (36 - len(project_name))
            line += "%s" % assy_name
            if args.used_by is not None:
                assy = project.assemblies[assy_name]
                line += "(%d)" % assy.count
                assy_count = assy_count + assy.count
            line += " " * (36 - len(assy_name))
            if (
                project.config_obj["assemblies"][assy_name] is not None
                and "desc" in project.config_obj["assemblies"][assy_name]
            ):
                line += "%s" % project.config_obj["assemblies"][assy_name]["desc"]
            print(line)
            assy_kinds = assy_kinds + 1

    if assy_kinds > 0:
        if args.used_by is None:
            print("Total: %d" % assy_kinds)
        else:
            print("Total: %d assemblies of %d kinds" % (assy_count, assy_kinds))
    else:
        print("\t<none>")
