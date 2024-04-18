#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-04-17
#
# Licensed under Apache License, Version 2.0.
#

import typing


class FileFactory:
    path: typing.Optional[str] = None

    def __init__(self, ctx, project, config):
        self.config = config
        self.ctx = ctx
        self.project = project

    async def download(self, path):
        raise NotImplementedError(
            "FileFactory.download is implemented in child classes"
        )
