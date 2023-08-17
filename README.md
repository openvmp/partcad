=======
PartCAD
=======

This is a framework for maintaining information about mechanical parts and how they come together to form larger models.

## Modelling

This frameworks allows to create large models and scenes, one part at a time, while having parts and assemblies often 

### Parts

Individual parts can be defined using the following methods:

- STEP file
- STL file
- CadQuery script
    - Original CadQuery Gateway Interface
    - Extension for parametrized CadQuery scripts

### Part repositories

PartCAD supports accessing repositories of parts using the following methods:

- Local files (present in your own source code repository)
- External GIT repository (HTTPS, SSH)
- External tar ball (HTTPS)

### Assemblies

Assemblies are defined as parametrized instructions how to put parts and other assemblies together.
Assembly parameters can be of two kinds: build time and run time.

Assemblies with different build time parameters are different assemblies, different models.

Assemblies with different run time parameters are the same assembly, just visualized in a different state (e.g. motion state).

### Scenes

Scenes are defined as parametrized instructions how to place assemblies relative to each other for visualization purposes.

## Export

### Visualization

Individual parts, assemblies and scenes can be rendered and exported into the following formats:

- PNG
- STL

### Other modelling formats

Additionally, assemblies and scenes will be (in progress) exported into the following formats:

- SDF

### Purchasing / Bill of materials

The bill of materials for each assembly can be produced using the following formats:

- CSV
- Markdown
