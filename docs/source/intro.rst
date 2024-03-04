Introduction
############

==========
Background
==========

PartCAD has begun as an internal tool in the
`OpenVMP project <https://github.com/openvmp/openvmp>`_
to maintain the blueprints of OpenVMP robots in a way, that allows reconfiguring
the blueprints based on the specific needs (parameters), and allows to maintain
the bill of materials and all the neccessary data to purchase the required parts.

Since then PartCAD has evolved into a standalone framework that is available for
any project to use. It does not aim to replace the existing part and CAD model
databases, but it does aim to introduce structure and strict version control to
enable professional workflows at scale and high velocity.

========
Overview
========

PartCAD can be perceived as consisting of four parts:

- PartCAD standards and conventions on how to maintain part and assembly data

- The public repository of data created and maintained by the community based
  on the PartCAD standards and conventions

- Tools that operate with public and private repositories for as
  long as they are maintained in accordance with the PartCAD standards and
  conventions

- Libraries and frameworks to programmatically interact with PartCAD data in
  public and private repositories 

Depending on the specific use case, different parts of PartCAD need to be
studies. All common use cases are briefly described in the 'Use cases' section.
Detailed documentation on each part of PartCAD follows after that.