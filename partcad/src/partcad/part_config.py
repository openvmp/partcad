#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-26
#
# Licensed under Apache License, Version 2.0.
#

from .shape_config import ShapeConfiguration


class PartConfiguration(ShapeConfiguration):
    def __init__(self, name, config):
        super().__init__(name, config)

    @staticmethod
    def normalize(name, config):
        if isinstance(config, str):
            # This is a short form alias
            config = {"type": "alias", "target": config}

        if "params" in config:
            for param_name, param_value in config["params"].items():
                if isinstance(param_value, str):
                    config["params"][param_name] = {
                        "type": "string",
                        "default": param_value,
                    }
                elif isinstance(param_value, float):
                    config["params"][param_name] = {
                        "type": "int",
                        "default": param_value,
                    }
                elif isinstance(param_value, int):
                    config["params"][param_name] = {
                        "type": "float",
                        "default": param_value,
                    }

        return ShapeConfiguration.normalize(name, config)
