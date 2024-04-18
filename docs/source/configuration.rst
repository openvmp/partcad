Configuration
#############

========
Packages
========

The package is described using the configuration file ``partcad.yaml`` placed
in the package folder.
Besides the list of imported dependencies, it declares parts and assemblies.


  .. code-block:: yaml 

    desc: <(optional) description>
    url: <(optional) package or maintainer's url>
    poc: <(optional) point of contact, maintainer's email>
    partcad: <(optional) required PartCAD version spec string>
    pythonVersion: <(optional) python version for sandboxing if applicable>
    pythonRequirements: <(python scripts only) the list of dependencies to install>

    import:
        <dependency-name>:
            desc: <(optional) textual description>
            type: <(optional) git|tar|local, can be guessed by path or url>
            path: <(local only) relative path to the package>
            url: <(git|tar only) URL of the package>
            relPath: <(git|tar only) relative path within the repository>
            revision: <(git only) the exact revision to import>

    parts:
        <part declarations, see below>

    assemblies:
        <assembly declarations, see below>

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
|                    |       path: ../../other                                                                               |
+--------------------+-------------------------------------------------------------------------------------------------------+
| GIT repository     | .. code-block:: yaml                                                                                  |
| :raw-html:`<br />` |                                                                                                       |
| (HTTPS, SSH)       |   import:                                                                                             |
|                    |     other_repo:                                                                                       |
|                    |         url: https://github.com/openvmp/partcad                                                       |
|                    |         relPath: examples  # where to "cd"                                                            |
+--------------------+-------------------------------------------------------------------------------------------------------+
| Hosted tar ball    | .. code-block:: yaml                                                                                  |
| :raw-html:`<br />` |                                                                                                       |
| (HTTPS)            |   import:                                                                                             |
|                    |     other_archive:                                                                                    |
|                    |       url: https://github.com/openvmp/partcad/archive/7544a5a1e3d8909c9ecee9e87b30998c05d090ca.tar.gz |
+--------------------+-------------------------------------------------------------------------------------------------------+

=====
Parts
=====

Parts are declared in ``partcad.yaml`` using the following syntax:

  .. code-block:: yaml

    parts:
      <part name>:
        type: <openscad|cadquery|build123d|ai-openscad|ai-cadquery|ai-build123d|step|stl|3mf>
        desc: <(optional) textual description, also used by AI>
        path: <(optional) the source file path, "{part name}.{ext}" otherwise>
        <... type-specific options ...>
        offset: <OCCT Location object, e.g. "[[0,0,0], [0,0,1], 0]">

Depending on the type of the part, the configuration may have different options:

  .. code-block:: yaml

    parts:
      <part name>:
        type: <openscad|cadquery|build123d>
        cwd: <alternative current working directory>
        patch:
          <...regexp substitutions to apply...>
          "patern": "repl"
        pythonRequirements: <(python scripts only) the list of dependencies to install>
        parameters:
          <param name>:
            type: <str|float|int|bool>
            default: <default value>

  .. code-block:: yaml

    parts:
      <part name>:
        type: <ai-openscad|ai-cadquery|ai-build123d>
        provider: <the model provider to use, google|openai>
        tokens: <the limit of token context>
        top_p: <(openai only) the top_p parameter>
        images: <representative images as input for AI>
          - <image path>

  .. code-block:: yaml

    parts:
      <part name>:
        type: stl
        binary: <use the binary format>

When the source file (`path`) is not present but needs to be pulled
from a remote location, the following options can be used:

  .. code-block:: yaml

    fileFrom: url
    fileUrl: <url to pull the file from>
    # fileCompressed: <(optional) whether the file needs to be decompressed before use>
    # fileMd5Sum: <(optional) the MD5 checksum of the file>
    # fileSha1Sum: <(optional) the SHA1 checksum of the file>
    # fileSha2Sum: <(optional) the SHA2 checksum of the file>

Here are some examples:

+--------------------------------------------------------------------------------------+---------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Example                                                                              | Configuration             | Result                                                                                                                  |
+======================================================================================+===========================+=========================================================================================================================+
|                                                                                      | .. code-block:: yaml      | .. image:: https://github.com/openvmp/partcad/blob/main/examples/produce_part_ai_cadquery/cube.svg?raw=true             |
|| AI-generated                                                                        |                           |   :width: 128                                                                                                           |
|| CadQuery or                                                                         |   parts:                  |                                                                                                                         |
|| OpenSCAD script                                                                     |     cube:                 |                                                                                                                         |
|                                                                                      |       type: ai-cadquery   |                                                                                                                         |
|                                                                                      |       # type: ai-openscad |                                                                                                                         |
|                                                                                      |       desc: A cube        |                                                                                                                         |
+--------------------------------------------------------------------------------------+---------------------------+-------------------------------------------------------------------------------------------------------------------------+
|                                                                                      | .. code-block:: yaml      | .. image:: https://github.com/openvmp/partcad/blob/main/examples/produce_part_cadquery_primitive/cylinder.svg?raw=true  |
|| `CadQuery <https://github.com/CadQuery/cadquery>`_ or                               |                           |   :width: 128                                                                                                           |
|| `build123d <https://github.com/gumyr/build123d>`_ script                            |   parts:                  |                                                                                                                         |
|| in ``src/cylinder.py``                                                              |     src/cylinder:         |                                                                                                                         |
|                                                                                      |       type: cadquery      |                                                                                                                         |
|                                                                                      |       # type: build123d   |                                                                                                                         |
+--------------------------------------------------------------------------------------+---------------------------+-------------------------------------------------------------------------------------------------------------------------+
|| `OpenSCAD <https://en.wikipedia.org/wiki/OpenSCAD>`_ script                         | .. code-block:: yaml      | .. image:: https://github.com/openvmp/partcad/blob/main/examples/produce_part_openscad/cube.svg?raw=true                |
|| in ``cube.scad``                                                                    |                           |   :width: 128                                                                                                           |
|                                                                                      |   parts:                  |                                                                                                                         |
|                                                                                      |     cube:                 |                                                                                                                         |
|                                                                                      |       type: scad          |                                                                                                                         |
+--------------------------------------------------------------------------------------+---------------------------+-------------------------------------------------------------------------------------------------------------------------+
|| CAD file                                                                            | .. code-block:: yaml      | .. image:: https://github.com/openvmp/partcad/blob/main/examples/produce_part_step/bolt.svg?raw=true                    |
|| (`STEP <https://en.wikipedia.org/wiki/ISO_10303>`_ in ``screw.step``,               |                           |   :width: 128                                                                                                           |
|| `STL <https://en.wikipedia.org/wiki/STL_(file_format)>`_ in ``screw.stl``,          |   parts:                  |                                                                                                                         |
|| or `3MF <https://en.wikipedia.org/wiki/3D_Manufacturing_Format>`_ in ``screw.3mf``) |     screw:                |                                                                                                                         |
|                                                                                      |       type: step          |                                                                                                                         |
|                                                                                      |       # type: stl         |                                                                                                                         |
|                                                                                      |       # type: 3mf         |                                                                                                                         |
+--------------------------------------------------------------------------------------+---------------------------+-------------------------------------------------------------------------------------------------------------------------+

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

==========
Assemblies
==========

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

Other methods to define assemblies are coming soon (e.g. using ``CadQuery`` or ``build123d``).

It is also possible to declare assemblies in ways that piggyback on assemblies that are
already defined elsewhere. Unfortunately, "enrich" is not yet implemented for
assemblies.

+---------+--------------------------------------------+----------------------------+
| Method  | Configuration                              | Description                |
+=========+============================================+============================+
| Alias   | .. code-block:: yaml                       || Create a shallow          |
|         |                                            || clone of the              |
|         |   assemblies:                              || existing assembly.        |
|         |     <alias-name>:                          || For example, to           |
|         |       type: alias                          || make it easier to         |
|         |       source: </path/to:existing-assembly> || reference it locally.     |
+---------+--------------------------------------------+----------------------------+
