Tutorial
########

============
Command Line
============

Create a package
----------------

First, the current directory needs to be initialized as a PartCAD package.

  .. code-block:: shell

    # Initialize new PartCAD package in the current folder
    pc init

If there is no ``-p`` flag passed to ``pc init``
then the dependency on the public PartCAD repository is added automatically.

Alternatively, manually create ``partcad.yaml`` with the following content:

  .. code-block:: yaml

    # partcad.yaml
    import:
      # Public PartCAD repository (reference it explicitly if required)
      pub:
        type: git
        url: https://github.com/openvmp/partcad-index.git

Now launch ``pc list`` to see the list of packages currently available in
the public PartCAD repository.

  .. code-block:: shell

    # Recursively iterate over all dependencies of the current package
    pc list

Manage dependencies
-------------------

PartCAD has to be provided with a configuration file which may declare parts and
assemblies, but also declares all repositories that PartCAD is allowed to query.

PartCAD has no implicit dependencies built in,
so a dependency on the public PartCAD repository needs to be added
if PartCAD is supposed to query it.

In the newly created package, comment out the "pub" dependency (prepend ``#``)
and see how the output of ``pc list`` changes.

Add a part
----------

Let's add a part defined using an OpenSCAD script.

First, create the OpenSCAD script which defines a cube of size 10mm.

  .. code-block:: shell

    # Create "test.scad"
    echo "translate (v= [0,0,0])  cube (size = 10);" > test.scad

Now let's add a declaration of this part to ``partcad.yaml``.

  .. code-block:: shell

    pc add-part scad test.scad


Inspect the part
----------------

Once a part is created, it can be inspect in ``OCP CAD Viewer``.

  .. code-block:: shell

    pc inspect :test

Export the part
---------------

Now the part can be exported:

  .. code-block:: shell

    pc render -t stl :test

=================
VS Code Extension
=================

Start new workspace
-------------------

Open Visual Studio Code and create a new empty workspace.

Activate Python
---------------

If necessary, install the Python extension.
Activate a Python environment (any version from 3.9 to 3.11).

Install the extension
---------------------

Install the
`PartCAD <https://marketplace.visualstudio.com/items?itemName=OpenVMP.partcad>`_
extension from the VS Code marketplace.

Install PartCAD
---------------

Switch to the PartCAD workbench
(look for the PartCAD logo at the left edge of the screen).
There is the PartCAD Explorer view on the left.
Click ``Install PartCAD`` in the Explorer view if this button is shown
to install PartCAD in the activated Python environment.

Create a package
----------------

Once PartCAD is initialized, it won't detect any PartCAD package in the empty
workspace.
Click ``Initialize Package`` to create ``partcad.yaml``.

Browse
------

Browse the imported packages in the Explorer view. Click on the parts and
assemblies to see them in ``OCP CAD Viewer`` view that will appear on the right.

Create a part
-------------

Click ``Add a CAD script`` in the Explorer view toolbar.
Select the script type from the dropdown list. Then select the template to use.
An editor view with the newly created script will be shown.

Inspect the part
----------------

Press ``Save`` (Ctrl-S or Cmd-S) to save the script and to trigger an automatic
inspection of the part. ``OCP CAD Viewer`` view will appear on the right.