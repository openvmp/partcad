# PartCAD <!-- omit in toc -->

[![License](https://github.com/openvmp/partcad/blob/main/apache20.svg?raw=true)](./LICENSE.txt)

[![CI on Linux, MacOS and Windows](https://github.com/openvmp/partcad/actions/workflows/python-test.yml/badge.svg)](https://github.com/openvmp/partcad/actions/workflows/python-test.yml)
[![CD on Linux, MacOS and Windows](https://github.com/openvmp/partcad/actions/workflows/python-build.yml/badge.svg)](https://github.com/openvmp/partcad/actions/workflows/python-build.yml)
[![Deployment to PyPI](https://github.com/openvmp/partcad/actions/workflows/python-deploy.yml/badge.svg)](https://github.com/openvmp/partcad/actions/workflows/python-deploy.yml)
[![Documentation Status](https://readthedocs.org/projects/partcad/badge/?version=latest)](https://partcad.readthedocs.io/en/latest/?badge=latest)
<a href="https://discord.gg/AXbP47zYw5"><img alt="Discord" src="https://img.shields.io/discord/1091497262733074534?logo=discord&logoColor=white&label=Discord&labelColor=353c43&color=31c151"></a>

PartCAD is the first build system and package manager for CAD models,
and a framework for creating assemblies.

PartCAD allows to maintain information about mechanical parts,
how they come together to form larger assemblies,
and to reuse the same parts in multiple assemblies, multiple projects.
The implementation of parts can change over time
(e.g. optimize or migrate to [build123d] from [STEP]) without the need to update
all of the consumers.

Find [more documentation here](https://partcad.readthedocs.io/en/latest/?badge=latest).

## Installation

The recommended method to install PartCAD for most users is:

```shell
pip install partcad-cli
```

For contributors:

```shell
git clone https://github.com/openvmp/partcad.git
cd partcad
python3 -m pip install -e ./partcad
python3 -m pip install -e ./partcad-cli
```

PartCAD works best when [conda](https://docs.conda.io/) is installed.
If that doesn't help (e.g. MacOS+arm64) then try ``mamba``.
On Windows, PartCAD requires at least a `conda` environment.

## Architecture

![Architecture](https://github.com/openvmp/partcad/blob/main/docs/source/architecture.png?raw=true)

## Tools for mechanical engineering

Here is an overview of the open source tools to maintain
mechanical projects. It shows where does this framework fit
in the modern mechanical development workflows.

```mermaid
flowchart TB

subgraph repo["Your project's GIT repository"]
  subgraph custom_repo["Custom parts"]
    direction TB
    custom_part_internet["A STEP file\ndownloaded from Internet\nor the vendor site"]
    custom_part_cad["A part exported as a solid\nfrom a CAD tool not\nsuitable for collaboration"]
    custom_part_cq["An individual reusable part\nmaintained as a script\nunder a version control system"]
    custom_part_os["Another reusable part\nmaintained as a script\nunder a version control system"]
  end

  model["Your project's model defined\nas ASSY or Python code\nfor version control\nand collaboration"]

  subgraph scenes["Scenes"]
    test1["Capability 1\ntest scene"]
    test2["Capability 2\ntest scene"]
  end
end

subgraph external_repos["Third-party GIT repositories,\nCDN-hosted files or OCCI servers"]
  subgraph external_repo["Repository of standard\nor popular parts"]
  end
end

subgraph external_tools["External tools"]
  freecad["FreeCAD"]
  cadquery["CadQuery / build123d"]
  openscad["OpenSCAD"]
  gazebo["Gazebo"]

  partcad["PartCAD library"]
  style partcad fill:#c00
end

custom_part_cad <--- |Individual\ncontributor|freecad
custom_part_cq <--- |Part design\nworkflow| cadquery
custom_part_os <--- |Part design\nworkflow| openscad

external_repo ---> |Import| model
custom_repo ---> |Import| model
model -.-> |Import| test1
model -.-> |Import| test2

custom_repo <-. Maintained\nusing\nPartCAD\nconvention .- partcad
external_repo <-. Maintained\nusing\nPartCAD\nconvention .- partcad
model <--- partcad
test1 <--- partcad
test2 <--- partcad

test1 -.-> |Export| gazebo
test2 -.-> |Export| gazebo
```

[CadQuery]: https://github.com/CadQuery/cadquery
[build123d]: https://github.com/gumyr/build123d
[STEP]: https://en.wikipedia.org/wiki/ISO_10303
[OpenCASCADE]: https://www.opencascade.com/
