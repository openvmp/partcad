from build123d import Location

from .context import (
    Context,
    init,
    get_part,
    get_assembly,
    finalize,
    finalize_real,
    _partcad_context,
    render,
)
from .consts import THIS
from .assembly import Assembly
from .part import Part
from .project_factory_local import ProjectFactoryLocal
from .project_factory_git import ProjectFactoryGit
from .project_factory_tar import ProjectFactoryTar
from .cli import main as main_cli
from .user_config import user_config


__all__ = [
    "config",
    "context",
    "shape",
    "part",
    "part_factory",
    "part_factory_step",
    "part_factory_cadquery",
    "project",
    "project_factory",
    "project_factory_local",
    "project_factory_git",
    "project_factory_tar",
    "assembly",
    "assembly_factory",
    "assembly_factory_python",
    "scene",
    "main_cli",
]

__version__: str = "0.2.9"
