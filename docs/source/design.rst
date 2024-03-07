Design
######

.. image:: ./images/architecture.png

=========================
Standards and conventions
=========================

Packages
--------

All data in PartCAD is bundled into 'packages'.
Packages are organized in a hierarchical structure where some packages may
"import" a list of other packages.
The top-level package is called "/". If a package called "/package" imports a
child package called "sub-package" then such package will be called
"/package/sub-package".

The package is described using the configuration file ``partcad.yaml`` placed
in the package folder.
Besides the list of imported dependencies, it declares the parts and assemblies
defined in this package.
The configuration file syntax is as follows:


  .. code-block:: yaml 

    desc: <description>
    partcad: <required PartCAD version spec string>

    import:
        sub-package-name:
            desc: <(optional) textual description>
            type: <git|tar|local>
            path: <(local only) relative path>
            url: <(git|tar only) URL of the package>
            relPath: <(git|tar only) relative path within the repository>
            revision: <(git only) the exact revision to import>
            web: <(optional) package or maintainer's url>
            poc: <(optional) maintainer's email>
            pythonVersion: <(optional) python version for sandboxing if applicable>

    parts:
        <part declarations are placed here>

    assemblies:
        <assembly declarations are placed here>

Here are some ``import`` examples:

.. role:: raw-html(raw)
    :format: html

+--------------------+-------------------------------------------------------------------------------------------------------+
| Method             | Example                                                                                               |
+====================+=======================================================================================================+
|| Local files       | .. code-block:: yaml                                                                                  |
|| (in the same      |                                                                                                       |
|| source code       |   import:                                                                                             |
|| repository)       |     other_directory:                                                                                  |
|                    |       type: local                                                                                     |
|                    |       path: ../../other                                                                               |
+--------------------+-------------------------------------------------------------------------------------------------------+
| GIT repository     | .. code-block:: yaml                                                                                  |
| :raw-html:`<br />` |                                                                                                       |
| (HTTPS, SSH)       |   import:                                                                                             |
|                    |     other_directory:                                                                                  |
|                    |         url: https://github.com/openvmp/partcad                                                       |
|                    |         relPath: examples  # where to "cd"                                                            |
+--------------------+-------------------------------------------------------------------------------------------------------+
| Hosted tar ball    | .. code-block:: yaml                                                                                  |
| :raw-html:`<br />` |                                                                                                       |
| (HTTPS)            |   import:                                                                                             |
|                    |     other_directory:                                                                                  |
|                    |       type: tar                                                                                       |
|                    |       url: https://github.com/openvmp/partcad/archive/7544a5a1e3d8909c9ecee9e87b30998c05d090ca.tar.gz |
+--------------------+-------------------------------------------------------------------------------------------------------+

Parts
-----

PartCAD has an evergrowing list of ways to define the part model:

- `STEP <https://en.wikipedia.org/wiki/ISO_10303>`_
- `STL <https://en.wikipedia.org/wiki/STL_(file_format)>`_
- `3MF <https://en.wikipedia.org/wiki/3D_Manufacturing_Format>`_
- `OpenSCAD <https://en.wikipedia.org/wiki/OpenSCAD>`_
- `CadQuery <https://github.com/CadQuery/cadquery>`_
- `build123d <https://github.com/gumyr/build123d>`_

Parts are declared in ``partcad.yaml`` using the following syntax:

  .. code-block:: yaml

    parts:
      <part name>:
        type: <openscad|cadquery|build123d|step|stl|3mf>
        path: <(optional) the source file path>
        binary: <(stl only) use the binary format>
        parameters:  # OpenSCAD, CadQuery and build123d only
          <param name>:
            type: <str|float|int|bool>
            default: <default value>
        offset: <OCCT Location object, e.g. "[[0,0,0], [0,0,1], 0]">

Here are some examples:

+--------------------------------------------------------------------------------------+-------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Example                                                                              | Configuration           | Result                                                                                                                  |
+======================================================================================+=========================+=========================================================================================================================+
|                                                                                      | .. code-block:: yaml    | .. image:: https://github.com/openvmp/partcad/blob/main/examples/produce_part_cadquery_primitive/cylinder.svg?raw=true  |
|| `CadQuery <https://github.com/CadQuery/cadquery>`_ or                               |                         |   :width: 128                                                                                                           |
|| `build123d <https://github.com/gumyr/build123d>`_ script                            |   parts:                |                                                                                                                         |
|| in ``src/cylinder.py``                                                              |     src/cylinder:       |                                                                                                                         |
|                                                                                      |       type: cadquery    |                                                                                                                         |
|                                                                                      |       # type: build123d |                                                                                                                         |
+--------------------------------------------------------------------------------------+-------------------------+-------------------------------------------------------------------------------------------------------------------------+
|| `OpenSCAD <https://en.wikipedia.org/wiki/OpenSCAD>`_ script                         | .. code-block:: yaml    | .. image:: https://github.com/openvmp/partcad/blob/main/examples/produce_part_scad/cube.svg?raw=true                    |
|| in ``cube.scad``                                                                    |                         |   :width: 128                                                                                                           |
|                                                                                      |   parts:                |                                                                                                                         |
|                                                                                      |     cube:               |                                                                                                                         |
|                                                                                      |       type: scad        |                                                                                                                         |
+--------------------------------------------------------------------------------------+-------------------------+-------------------------------------------------------------------------------------------------------------------------+
|| CAD file                                                                            | .. code-block:: yaml    | .. image:: https://github.com/openvmp/partcad/blob/main/examples/produce_part_step/bolt.svg?raw=true                    |
|| (`STEP <https://en.wikipedia.org/wiki/ISO_10303>`_ in ``screw.step``,               |                         |   :width: 128                                                                                                           |
|| `STL <https://en.wikipedia.org/wiki/STL_(file_format)>`_ in ``screw.stl``,          |   parts:                |                                                                                                                         |
|| or `3MF <https://en.wikipedia.org/wiki/3D_Manufacturing_Format>`_ in ``screw.3mf``) |     screw:              |                                                                                                                         |
|                                                                                      |       type: step        |                                                                                                                         |
|                                                                                      |       # type: stl       |                                                                                                                         |
|                                                                                      |       # type: 3mf       |                                                                                                                         |
+--------------------------------------------------------------------------------------+-------------------------+-------------------------------------------------------------------------------------------------------------------------+

Other methods to define parts are coming soon (e.g. `SDF <https://github.com/fogleman/sdf>`_).

It is also possible to declare parts in ways that piggyback on parts that are
already defined elsewhere.

+---------+----------------------------------------+----------------------------+
| Method  | Configuration                          | Description                |
+=========+========================================+============================+
| Alias   | .. code-block:: yaml                   || Create a shallow          |
|         |                                        || clone of the              |
|         |   parts:                               || existing part.            |
|         |     <alias-name>:                      || For example, to           |
|         |       type: alias                      || make it easier to         |
|         |       source: </path/to:existing-part> || reference it locally.     |
+---------+----------------------------------------+----------------------------+
| Enrich  | .. code-block:: yaml                   || Create an opinionated     |
|         |                                        || alternative to the        |
|         |   parts:                               || existing part by          |
|         |     <enriched-part-name>:              || initializing some of      |
|         |       type: enrich                     || its parameters, and       |
|         |       source: </path/to:existing-part> || overriding any of its     |
|         |       with:                            || properties. For           |
|         |         <param1>: <value1>             || example, to avoid         |
|         |         <param2>: <value2>             || passing the same set      |
|         |       offset: <OCCT-Location-obj>      || of parameters many times. |
+---------+----------------------------------------+----------------------------+

Assemblies
----------

Assemblies are parametrized instructions on how to put parts and other
assemblies together.

PartCAD is expected to have an ever-growing list of ways to define assemblies
using existing parts.
However, at the moment, only one way is supported.
It is called ASSY: assembly YAML.
The idea behind ASSY is to create a simplistic way to enumerate parts,
define their parameters and define how parts connect.

Assemblies are declared in ``partcad.yaml`` using the following syntax:

  .. code-block:: yaml

    assemblies:
      <assembly name>:
        type: assy
        path: <(optional) the source file path>
        parameters:  # (optional)
          <param name>:
            type: <str|float|int|bool>
            default: <default value>
        offset: <OCCT Location object, e.g. "[[0,0,0], [0,0,1], 0]">

Here is an example:

+---------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Configuration                                     | Result                                                                                                                  |
+===================================================+=========================================================================================================================+
| .. code-block:: yaml                              | .. image:: https://github.com/openvmp/partcad/blob/main/examples/produce_assembly_assy/logo.svg?raw=true                |
|                                                   |   :width: 400                                                                                                           |
|   # partcad.yaml                                  |                                                                                                                         |
|   assemblies:                                     |                                                                                                                         |
|    logo:                                          |                                                                                                                         |
|      type: assy                                   |                                                                                                                         |
|                                                   |                                                                                                                         |
|   # logo.assy                                     |                                                                                                                         |
|   links:                                          |                                                                                                                         |
|   - part: /produce_part_cadquery_logo:bone        |                                                                                                                         |
|     location: [[0,0,0], [0,0,1], 0]               |                                                                                                                         |
|   - part: /produce_part_cadquery_logo:bone        |                                                                                                                         |
|     location: [[0,0,-2.5], [0,0,1], -90]          |                                                                                                                         |
|   - links:                                        |                                                                                                                         |
|     - part: /produce_part_cadquery_logo:head_half |                                                                                                                         |
|       name: head_half_1                           |                                                                                                                         |
|       location: [[0,0,2.5], [0,0,1], 0]           |                                                                                                                         |
|     - part: /produce_part_cadquery_logo:head_half |                                                                                                                         |
|       name: head_half_2                           |                                                                                                                         |
|       location: [[0,0,0], [0,0,1], -90]           |                                                                                                                         |
|     name: {{name}}_head                           |                                                                                                                         |
|     location: [[0,0,25], [1,0,0], 0]              |                                                                                                                         |
|   - part: /produce_part_step:bolt                 |                                                                                                                         |
|     location: [[0,0,7.5], [0,0,1], 0]             |                                                                                                                         |
+---------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------+

Other methods to define assemblies are coming soon (e.g. using ``CadQuery``).

It is also possible to declare parts in ways that piggyback on parts that are
already defined elsewhere. Unfortunately, "enrich" is not yet implemented for
assemblies.

+---------+--------------------------------------------+----------------------------+
| Method  | Configuration                              | Description                |
+=========+============================================+============================+
| Alias   | .. code-block:: yaml                       || Create a shallow          |
|         |                                            || clone of the              |
|         |   assemblies                               || existing assembly.        |
|         |     <alias-name>:                          || For example, to           |
|         |       type: alias                          || make it easier to         |
|         |       source: </path/to:existing-assembly> || reference it locally.     |
+---------+--------------------------------------------+----------------------------+

Scenes
------

PartCAD does not yet implement scenes. But the idea is to be able to reproduce
the same features as worlds in Gazebo to the extent that PartCAD scenes can be
exported to and simulated in Gazebo, but without using XML while creating the
scene.

Monorepos
---------

When PartCAD is initialized, the current folder and its ``partcad.yaml`` become
the `current` package, but not the `root` package. The root package is
discovered by traversing the parent directories for as long as there is another
``partcad.yaml`` found there.

This allows to run PartCAD tools from any sub-directory in a monorepo project
while maintaining the same meaning of relative and absolute paths.

Paths
-----

PartCAD uses package paths to identify packages and parts declared in them.

The current package has the path ``""`` or ``"."``.
The root package has the path ``"/"``.
For any package ``"<package-path>"``, each sub-directory containing
``partcad.yaml`` and each ``import``-ed dependency becomes
``"<package-path>/<sub-package>"``.

The complete path of a part or assembly is the combination of the package path
and the item name: ``<package-path>:<part-name>`` or
``<package-path>:<assembly-name>``.

For parametrized parts, the parameter values can be appended to the part name
after ``;``:

  .. code-block:: shell

    # Instead of:
    pc inspect \
        -p length=30 \
        -p size=M4-0.7 \
        /pub/std/metric/cqwarehouse:fastener/hexhead-din931

    # Use this:
    pc inspect /pub/std/metric/cqwarehouse:fastener/hexhead-din931;length=30,size=M4-0.7

=====================
The public repository
=====================

The public PartCAD repository is created and maintained by the community
based on the PartCAD standards and conventions. It is hosted on
`GitHub <https://github.com/openvmp/partcad-index>`_.

The top levels of the package hierarchy are expected to be maintained by the
PartCAD community.
Lower levels of the hierarchy are expected to be maintained by vendors and
other communities. PartCAD community does not aim to achieve the
uniqueness of parts and assemblies. Moreover, everyone is invited to provide
their alternative models as long as they provide a different level of model
quality or different level of package quality management processes, and as long
the package data properly reflects the quality that the maintainer provides and
commits to maintain. This way PartCAD users have a choice of which model to
use based on their specific needs.

=====
Tools
=====

PartCAD tools can operate with public and private repositories for as
long as they are maintained in accordance with the PartCAD standards and
conventions.

Command line tools
------------------

PartCAD CLI tools get installed using the PyPI module ``partcad-cli``.
The main tool is called ``pc``.
The CLI tools are supposed to provide the complete set of PartCAD features.

Visual Studio Code extension
----------------------------

PartCAD extension for ``vscode`` is designed to be the primary tool to


========================
Libraries and frameworks
========================

Python
------

The `partcad` Python module is the first PartCAD library. Its development is
prioritized due to the popularity and the value proposition of such Python
frameworks such as CadQuery and build123d.

Other languages
---------------

PartCAD does not aim to stop at supporting Python. Native libraries in other
languages are planned and all contributors wishing to join the project are
welcome.