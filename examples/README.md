# PartCAD Examples

## Publish (produce) models

There are many ways to produce a PartCAD model that can be consumed by others.

- Import parts defined using Python CAD frameworks:
  - [Primitive shapes using CadQuery](./produce_part_cadquery_primitive/)
  - [PartCAD logo using CadQuery](./produce_part_cadquery_logo/)
  - [Primitive shapes using build123d](./produce_part_build123d_primitive/)

- Import parts defined using CAD scripting languages:
  - [Primitive shapes using OpenSCAD](./produce_part_scad/)

- Import parts defined using CAD Files:
  - [STEP files](./produce_part_step/)
  - [STL files](./produce_part_stl/)
  - [3MF files](./produce_part_3mf/)

## Get (consume) existing models

There are many ways to consume existing modules:

- CLI: Export the model to a file:
  - `pc render -t step [<package-path>]:<part>`

- Visual Studio Code:  Show the model in OCP CAD Viewer:
  - `pc inspect [<package-path>]:<part>`

- Python scripts that use CadQuery:
  - [Import PartCAD parts in CadQuery scripts](./consume_cadquery/)

- Python scripts that use buid123d:
  - [Import PartCAD parts in buid123d scripts](./consume_build123d/)

- Any other Python script:
  - [Import PartCAD parts in Python scripts](./consume_standalone/)

## Features

These examples showcase particular PartCAD features:

- [Export to file](./feature_export)