############
Installation
############


Public PartCAD repository
=========================

The public PartCAD repository is hosted at [GitHub](https://github.com/openvmp/partcad-index).
If necessary, PartCAD tools are automatically retrieving the contents of this
repository and all other required repositories and packages. No manual action is needed is need to _install_ it.

However, if you suspect that something is wrong with locally cached files, feel free to delete the folder ~/.partcad.


Command line tools
==================

PartCAD command lines tools are implemented in Python and theoretically
available on all platforms where Python is available. However it is only getting
tested on Linux, MacOS and Windows.

.. code-block:: shell
    python -m pip install -U partcad-cli

The commands and options supported by PartCAD CLI:

.. code-block:: shell

    $ pc help
    usage: pc [-h] [-p CONFIG_PATH] {add,init,install,list,list-all,list-parts,list-assemblies,render,show} ...

    PartCAD command line tool

    positional arguments:
      {add,init,install,list,list-all,list-parts,list-assemblies,render,show}
        add                 Import a package
        init                Initialize new PartCAD package in this directory
        install             Download and prepare all imported packages
        list                List imported packages
        list-all            List available parts, assemblies and scenes
        list-parts          List available parts
        list-assemblies     List available assemblies
        render              Render the selected or all parts, assemblies and scenes in this package
        show                Visualize a part, assembly or scene

    options:
      -h, --help            show this help message and exit
      -p CONFIG_PATH        Package path (a YAML file or a directory with 'partcad.yaml')


Python module
=============

PartCAD provides a Python modules that can be used in CAD as code scripts
(such as CadQuery and build123d). It is a requirement for `partcad-cli` so it
doesn't usually need to be installed separately.

.. code-block:: shell

    python -m pip install -U partcad
