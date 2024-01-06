#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2023-12-23
#
# Licensed under Apache License, Version 2.0.
#

import logging
import os
import ruamel.yaml
import sys

import partcad as pc


def cli_help_add(subparsers):
    parser_add = subparsers.add_parser(
        "add",
        help="Import a package",
    )
    parser_add.add_argument(
        "alias",
        help="Alias to be used to reference the package",
        type=str,
    )
    parser_add.add_argument(
        "location",
        help="Path or URL to the package",
        type=str,
    )


def cli_add(args):
    if not os.path.exists("partcad.yaml"):
        logging.error("'partcad.yaml' not found!")
        sys.exit(1)

    if ":" in args.location:
        location_param = "url"
        if args.location.endswith(".tar.gz"):
            location_type = "tar"
        else:
            location_type = "git"
    else:
        location_param = "path"
        location_type = "local"

    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    with open("partcad.yaml") as fp:
        config = yaml.load(fp)
        fp.close()

    for elem in config:
        if elem == "import":
            imports = config["import"]
            imports[args.alias] = {
                location_param: args.location,
                "type": location_type,
            }
            break  # no need to iterate further
    with open("partcad.yaml", "w") as fp:
        yaml.dump(config, fp)
        fp.close()
