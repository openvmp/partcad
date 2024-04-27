# Example: feature\_interface

## Intro

This example demonstrates
how the same parametrized assembly can be defined in three slightly different ways
using three approaches to connect parts to each other.

`connect-ports` demonstrates how to connect ports to each other.

`connect-interfaces` demonstrates how to connect interfaces to each other.

`connect-mates` demonstrates how to provide the minimum information
while letting PartCAD determine the rest using the interfaces' mating metadata.

## Usage

```shell
pc inspect -a connect-ports
pc inspect -a connect-interfaces
pc inspect -a connect-mates

pc inspect -a -p placement=inner connect-ports
pc inspect -a -p placement=inner connect-interfaces
pc inspect -a -p placement=inner connect-mates
```
