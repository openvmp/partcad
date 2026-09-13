#
# PartCAD, 2026
#
# Licensed under Apache License, Version 2.0.
#

from .config import apply_user_parameter_overrides, normalize_parameters

# The section an interface declares its *construction* parameters in.
#
# Not 'parameters:', which an interface has had since interfaces existed and
# which means something else entirely there: the freedom of movement a
# connection made through the interface still has (see 'InterfaceParameter').
# The two cannot share a section, because their declarations look alike -
# '{min: 0, max: 10, default: 5}' is a perfectly good spelling of either - so
# one section holding both would have to guess, and guessing wrong is silent:
# an interface would be built from a default nobody set, and the parametrized
# reference to it would report a parameter it does declare as unknown.
#
# What is here is what a part's or a sketch's 'parameters:' is: typed values
# with defaults, replaced by name in a reference to the interface
# ('m-thru;size=4,depth=3') and substituted into the declaration wherever a
# '%...%' expression names one (see 'partcad.expr').
VARIABLES = "variables"


class InterfaceConfiguration:
    """Normalization of one interface declaration.

    Interfaces are not shapes - nothing constructs them, they have no factory
    and no cache - so they have no 'ShapeConfiguration'. What they do share
    with parts and sketches is the parameter section this normalizes: the short
    forms ('size: 3') expand to the long one, and the user's own configuration
    gets to override a default.
    """

    @staticmethod
    def normalize(name, config, object_name):
        if config is None:
            config = {}

        config["name"] = name
        if "orig_name" not in config:
            config["orig_name"] = name

        if config.get(VARIABLES):
            normalize_parameters(config[VARIABLES])
            apply_user_parameter_overrides(config, object_name, VARIABLES)

        return config
