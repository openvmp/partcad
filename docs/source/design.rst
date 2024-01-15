######
Design
######

Standards and conventions
=========================

Packages
--------

All CAD data in PartCAD is bundled into packages.
Packages are organized in a hierarchical structure where some packages "import"
a list of other packages.

Packages are expected to import all packages required to build the models
defined within themselves. But some packages may import other packages
exclusively for the purposes of making them discoverable (for example, the top
level of any PartCAD repository would usually contain a list of all packages
included in it, without defining any parts).

Parts
-----

PartCAD has an evergrowing list of ways to define the part model (STL, STEP,
OpenSCAD, CAD as code etc).

No matter which way is chosen, the part may have a list of parameters that the
consumer may provide.


Assemblies
----------

PartCAD is expected to have an evergrowing list of ways to define assemblies
using existing parts.
However, at the moment, only one way is supported.
It is called ASSY: assembly YAML.

The idea behind ASSY is an as simple way as possible to enumerate parts,
define their parameters and define how parts connect to each other.


Scenes
------

PartCAD does not yet implement scenes. But the idea is to be able to reproduce
the same features as worlds in Gazebo to the extent that PartCAD scenes can be
exported to and simulated in Gazebo, but without XML.


The public repository
=====================

The public PartCAD repository is created and maintained by the community
based on the PartCAD standards and conventions. It is hosted on
[Github](https://githud.com/openvmp/partcad).

Top levels of the package hierarchy are expected to be maintained by the
PartCAD community.
Lower levels of the hierarchy are expected to be maintained by vendors and
other services and communities. PartCAD community does not aim to achieve
uniqueness of parts and assemblies. Moreover, everyone is invited to provide
their alternative models as long as they provide a different level of model
quality or different level of package quality management processes, and as long
the package data properly reflects the quality that the maintainer provides and
commits to maintain. This way PartCAD consumers have a choice which models to
use based on their specific needs.

Tools
=====

Comman line tools
-----------------

PartCAD CLI tools can operate with public and private repositories for as
long as they are maintained in accordance with the PartCAD standards and
conventions


Libraries and frameworks
========================

Python
------

The `partcad` Python module is the first PartCAD library. Its development is
prioritized due to popularity and the value proposition of such Python
frameworks as CadQuery and build123d. 

Other languages
---------------

PartCAD does not aim to stop at supporting Python. Native libraries in other
languages are planned and all contributors wishing to join the project are
welcome.