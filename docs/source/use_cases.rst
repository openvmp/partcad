Use Cases
#########

PartCAD provides a public repository of parts and assemblies, and various tools
and frameworks to operate with those parts and assemblies.
Depending on particular goals, different ways of interacting with PartCAD tools
and data may be desired. Below is a list of some common use cases.

=======================
Browse available models
=======================

Online
------

The web UI to browse the public PartCAD repository will be available at ``partcad.org`` but, it is not yet published.

Visual Studio Code extension
----------------------------

The PartCAD extension is
[available](https://marketplace.visualstudio.com/items?itemName=OpenVMP.partcad>)
in VS Code extension marketplace.

### Command line tools

Whether you consder to publish new CAD models or consume already existing ones,
it makes senes to browse what's already available.

The PartCAD's integration into WebAssembly is not yet completed and, thus, there
is currently no public website where you can browse the public PartCAD
repository.

The command line tools is the easiest way to browse parts:

  .. code-block:: shell

    pc init # to initialize new PartCAD package in the current folder
    pc list # to list all available packages
    pc list-parts -r # to list all parts in all available packages
    pc list-assemblies -r # to list all assemblies in all available packages
    pc info /pub/std/metric/cqwarehouse:fastener/screw-buttonhead
    pc inspect /pub/std/metric/cqwarehouse:fastener/screw-buttonhead

The last command displays the chosen part in
``OCP CAD Viewer`` view in Visual Studio Code.
There is currently no support for ``cq-server``.
Please, let `support@partcad.org <mailto:support@partcad.org>`_ know if there is
any other tool we should support.

=============
Export models
=============

Individual parts, assemblies and scenes can be rendered and exported into the
following formats:

- Vector images

  - SVG

- Raster images

  - PNG

- 3D models

  - `STEP <https://en.wikipedia.org/wiki/ISO_10303>`_
  - `STL <https://en.wikipedia.org/wiki/STL_(file_format)>`_
  - `3MF <https://en.wikipedia.org/wiki/3D_Manufacturing_Format>`_
  - `ThreeJS <https://en.wikipedia.org/wiki/Three.js>`_
  - `OBJ <https://en.wikipedia.org/wiki/Wavefront_.obj_file>`_

Expect more output formats to be added to the list of supported export formats
in the future.

  .. code-block:: shell

    pc render -t stl <part path>
    pc render -t step -a <assembly path>

==============
Consume models
==============

CAD Design GUIs
---------------

If you want to use models from the public PartCAD repository in a CAD Design GUI
(like FreeCAD or its paid alternatives), the best way to do it at the moment
(before PartCAD plugins for these apps are available) is to export the models to
STEP or 3MF files and, then, import them into the CAD Design GUI of your choice.

  .. code-block:: shell

    # Some "export to a file" examples:
    pc render -t stl <part> [<package>]
    pc render -t step -a <assembly> [<package>]

Python: CadQuery
----------------

Here are some examples how to fetch PartCAD models from within a ``CadQuery``
script:

  .. code-block:: python

    # part.py
    import cadquery as cq
    import partcad as pc
    part = pc.get_part_cadquery(
        "/pub/std/metric/cqwarehouse:fastener/screw-buttonhead",
    )
    ...
    show_object(part)

  .. code-block:: python

    # assembly.py
    import cadquery as cq
    import partcad as pc
    assembly = pc.get_assembly_cadquery(
        "/pub/furniture/workspace/basic:imperial-desk-1",
    )
    ...
    show_object(assembly)

Python: build123d
-----------------

Here are some examples how to fetch PartCAD models from within a ``build123d``
script:

  .. code-block:: python

    # part.py
    import build123d as b3d
    import partcad as pc
    part = pc.get_part_build123d(
        "/pub/std/metric/cqwarehouse:fastener/screw-buttonhead",
    )
    ...
    show_object(part)

  .. code-block:: python

    # assembly.py
    import build123d as b3d
    import partcad as pc
    assembly = pc.get_assembly_build123d(
        "/pub/furniture/workspace/basic:imperial-desk-1",
    )
    ...
    show_object(assembly)

Python
------


  .. code-block:: python

    # part.py
    import partcad as pc

    part = pc.get_part(
        "/pub/std/metric/cqwarehouse:fastener/screw-buttonhead",
    )
    part.show()

  .. code-block:: python

    # assembly.py
    import partcad as pc

    assembly = pc.get_assembly(
        "/pub/furniture/workspace/basic:imperial-desk-1",
    )
    assembly.show()


shell
-----

  .. code-block:: shell
 
    # custom.sh
    for part in $PART_LIST; do
      pc render -t png $part 
    done

  .. code-block:: shell
 
    # custom.sh
    for assembly in $ASSEMBLY_LIST; do
      pc render -t png -a $assembly 
    done

==============
Produce models
==============

Files
-----

One way to define parts in PartCAD is by providing a file in any of the currently
supported formats: STEP, STL, 3MF. There is no intention to limit the list of
file formats supported. Contribute support of your favorite file format
(ideally, iimplicitly, by adding the corresponding support to build123d).

   .. code-block:: yaml

    # partcad.yaml
    parts:
        part1:
            type: step # part1.step is used
        part2:
            type: stl # part2.stl is used
        part3:
            type: 3mf # part3.3mf is used

CAD scripts
-----------

Another way to define parts is by using CAD scripting technologies such
as OpenSCAD. This is the only CAD scripting language supported at the moment.
The fundamental difference from CAD files listed above is the availability of
parameters. However OpenSCAD parameters are not yet supported.

  .. code-block:: yaml

    # partcad.yaml
    parts:
        part1:
            type: scad # part1.scad is used


Python scripts
--------------

The best way to define parts is by using modelling frameworks such as
CadQuery and build123d. PartCAD uses CQGI to load models
(in other words: intercepts `show_object()` calls).

  .. code-block:: python

    # partcad.yaml
    parts:
        part1:
            type: cadquery # part1.py is used
        optiona-path/part2:
            type: build123d # optional-path/part2.py is used

Assemblies
----------

  .. code-block:: yaml

    # partcad.yaml
    assemblies:
        logo:
            type: assy

  .. code-block:: yaml

    # logo.assy
    links:
      - part: bone
        package: example_part_cadquery_logo
        location: [[0,0,0], [0,0,1], 0]
      - part: bone
        package: example_part_cadquery_logo
        location: [[0,0,-2.5], [0,0,1], -90]
      - part: head_half
        package: example_part_cadquery_logo
        name: head_half_1
        location: [[0,0,27.5], [0,0,1], 0]
      - part: head_half
        package: example_part_cadquery_logo
        name: head_half_2
        location: [[0,0,25], [0,0,1], -90]
      - part: bolt
        package: example_part_step
        location: [[0,0,7.5], [0,0,1], 0]

==============
Publish models
==============

It's very simple to publish your package to the public PartCAD repository.
First, publish your package as a repo on GitHub.
Then create a pull request in
`the public PartCAD repo <https://github.com/openvmp/partcad-index>`_
to add a reference to your package.
