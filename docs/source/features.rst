Additional Features
###################

========
Security
========

As code-CAD is gaining popularity in the community, the topic of supply chain
security and the risk of running arbitrary third-party code is not sufficiently
addressed. PartCAD aims to close that gap for open-source software in a way
that exceeds anything commercial software has to offer at the moment.

PartCAD is capable of rendering scripted parts
(``CadQuery`` and ``build123d`` use Python) in sandboxed environments.

At the moment it is only useful from a dependency management perspective
(it allows third-party packages to bring their Python dependencies without
polluting your own Python environment),
in the future, PartCAD aims to achieve security isolation of the sandboxed
environments. That will fundamentally change the security implications of using
scripted models shared online.
