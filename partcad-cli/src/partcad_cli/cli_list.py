#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-23
#
# Licensed under Apache License, Version 2.0.
#

import time

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

    parser_list_parts.add_argument(
        "package",
        help="Package to retrieve the object from",
        type=str,
        nargs="?",
    )
    parser_list_assemblies.add_argument(
        "package",
        help="Package to retrieve the object from",
        type=str,
        nargs="?",
    )


def cli_list(args, ctx):
    pkg_count = 0

    projects = ctx.get_all_packages()
    projects = sorted(projects, key=lambda p: p["name"])

    # TODO(clairbee): remove the following workaround after replacing 'print'
    # with corresponding logging calls
    time.sleep(2)

    output = "PartCAD packages:\n"
    for project in projects:
        project_name = project["name"]

        line = "\t%s" % project_name
        padding_size = 60 - len(project_name)
        if padding_size < 4:
            padding_size = 4
        line += " " * padding_size
        line += "%s" % project["desc"]
        output += line + "\n"
        pkg_count = pkg_count + 1

    if pkg_count < 1:
        output += "\t<none>\n"
    pc.logging.info(output)


def cli_list_parts(args, ctx):
    part_count = 0
    part_kinds = 0

    if args.used_by is not None:
        pc.logging.info("Instantiating %s..." % args.used_by)
        ctx.get_assembly(args.used_by)
    else:
        ctx.get_all_packages()

    # TODO(clairbee): remove the following workaround after replacing 'print'
    # with corresponding logging calls
    time.sleep(2)

    output = "PartCAD parts:\n"
    for project_name in ctx.projects:
        if (
            hasattr(args, "package")
            and not args.package is None
            and args.package != project_name
        ):
            continue

        if project_name != ctx.get_current_project_path() and (
            not args.recursive
            and hasattr(args, "package")
            and args.package is None
        ):
            continue
        if project_name.startswith("partcad-"):
            continue
        project = ctx.projects[project_name]

        for part_name, part in project.parts.items():
            if args.used_by is not None and part.count == 0:
                continue

            line = "\t"
            if args.recursive:
                line += "%s" % project_name
                line += " " + " " * (35 - len(project_name))
            line += "%s" % part_name
            if args.used_by is not None:
                part = project.parts[part_name]
                line += "(%d)" % part.count
                part_count = part_count + part.count
            line += " " + " " * (35 - len(part_name))
            line += "%s" % part.desc
            output += line + "\n"
            part_kinds = part_kinds + 1

    if part_kinds > 0:
        if args.used_by is None:
            output += "Total: %d\n" % part_kinds
        else:
            output += "Total: %d parts of %d kinds\n" % (part_count, part_kinds)
    else:
        output += "\t<none>\n"
    pc.logging.info(output)


def cli_list_assemblies(args, ctx):
    assy_count = 0
    assy_kinds = 0

    if args.used_by is not None:
        print("Instantiating %s..." % args.used_by)
        # TODO(clairbee): do not call it twice in 'list-all'
        ctx.get_assembly(args.used_by)
    else:
        ctx.get_all_packages()

    # TODO(clairbee): remove the following workaround after replacing 'print'
    # with corresponding logging calls
    time.sleep(2)

    output = "PartCAD assemblies:\n"
    for project_name in ctx.projects:
        if (
            hasattr(args, "package")
            and not args.package is None
            and args.package != project_name
        ):
            continue

        if project_name != ctx.get_current_project_path() and (
            not args.recursive
            and hasattr(args, "package")
            and args.package is None
        ):
            continue
        if project_name.startswith("partcad-"):
            continue
        project = ctx.projects[project_name]

        for assy_name, assy in project.assemblies.items():
            if args.used_by is not None and assy.count == 0:
                continue

            line = "\t"
            if args.recursive:
                line += "%s" % project_name
                line += " " + " " * (35 - len(project_name))
            line += "%s" % assy_name
            if args.used_by is not None:
                assy = project.assemblies[assy_name]
                line += "(%d)" % assy.count
                assy_count = assy_count + assy.count
            line += " " + " " * (35 - len(assy_name))
            line += "%s" % assy.desc
            output += line + "\n"
            assy_kinds = assy_kinds + 1

    if assy_kinds > 0:
        if args.used_by is None:
            output += "Total: %d\n" % assy_kinds
        else:
            output += "Total: %d assemblies of %d kinds\n" % (
                assy_count,
                assy_kinds,
            )
    else:
        output += "\t<none>\n"
    pc.logging.info(output)
