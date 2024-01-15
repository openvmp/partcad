#########
Use cases
#########

PartCAD provides a public repository of parts and assemblies, and various tools
and frameworks to operate with those parts and assemblies.
Depending on particular goals, different ways of interacting with PartCAD tools
and data may be desired. Below is a list of some common use cases.

Browse available models
=======================

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
    pc show fastener/screw-buttonhead standard-metric-cqwarehouse

The last command displays the chosen part in
OCP CAD Viewer view in Visual Studio Code.

Consume models
==============

Python: CadQuery
----------------

.. code-block:: python

    # part.py
    import cadquery as cq
    import partcad as pc
    part = pc.get_part(
         # Part name
         "fastener/screw-buttonhead",
         # Package name
         "standard-metric-cqwarehouse",
    ).get_cadquery()
    ...
    show_object(part)<

.. code-block:: python

    # assembly.py
    import cadquery as cq
    import partcad as pc
    assembly = pc.get_assembly(
         # Assembly name
         "my_assembly",
         # Package name
         "my_package",
    ).get_cadquery()
    ...
    show_object(assembly)<

Python: build123d
-----------------

.. code-block:: python

    # part.py
    import build123d as b3d
    import partcad as pc
    part = pc.get_part(
         # Part name
         "fastener/screw-buttonhead",
         # Package name
         "standard-metric-cqwarehouse",
    ).get_build123d()
    ...
    show_object(part)

.. code-block:: python

    # assembly.py
    import build123d as b3d
    import partcad as pc
    assembly = pc.get_assembly(
         # Assembly name
         "my_assembly",
         # Package name
         "my_package",
    ).get_build123d()
    ...
    show_object(assembly)

Python
------


.. code-block:: python

    # part.py
    import partcad as pc

    if __name__ != "__cqgi__":
        from cq_server.ui import ui, show_object

    part = pc.get_part(
        # Part name
        "fastener/screw-buttonhead",
        # Package name
        "standard-metric-cqwarehouse",
    )
    pc.finalize(part, show_object)

.. code-block:: python

    # assembly.py
    import partcad as pc

    if __name__ != "__cqgi__":
        from cq_server.ui import ui, show_object

    assembly = pc.get_assembly(
        # Assembly name
         "my_assembly",
         # Package name
         "my_package",
    )
    pc.finalize(assembly, show_object)


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
            type: step # part1.step is expected
        part2:
            type: stl # part2.stl is expected
        part3:
            type: 3mf # part3.3mf is expected

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
            type: scad # part1.scad is expected


Python scripts
--------------

The best way to define parts is by using modelling frameworks such as
CadQuery and build123d. PartCAD uses CQGI to load models
(in other words: intercepts `show_object()` calls).

.. code-block:: python

    # partcad.yaml
    parts:
        part1:
            type: cadquery # part1.py is expected
        optiona-path/part2:
            type: build123d # optional-path/part2.py is expected

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