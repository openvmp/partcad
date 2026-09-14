#
# OpenVMP, 2023
#
# Author: Roman Kuzmenko
# Created: 2024-01-26
#
# Licensed under Apache License, Version 2.0.
#

import asyncio
import os
import random
import string
import typing

from partcad.shape_config_store import ShapeConfigStore

from . import logging as pc_logging
from . import tolerance_inspect


class _NoDefault:
    """Sentinel: an object-type parameter that has no default.

    For such a parameter, absent means absent - 'material' and 'color' either
    were declared or were not, and there is nothing sensible to invent for
    them. A parameter whose default is a real value (a 'tolerance' of 0.0)
    reads back as that value when nothing declared it.
    """

    def __repr__(self) -> str:
        return "NO_DEFAULT"


NO_DEFAULT = _NoDefault()


class _NotRead:
    """Sentinel: a file that has not been read for what it states yet.

    Distinct from None, which is the answer of a file that has been read and
    states nothing.
    """

    def __repr__(self) -> str:
        return "NOT_READ"


_NOT_READ = _NotRead()


def final_config(obj) -> dict:
    """The declaration an object resolves to, defensively.

    'get_final_config()' rather than 'config', so that an alias and an enrich
    answer for what they point at: neither says where a file comes from or what
    software it ships with, and reading their own configuration would find
    nothing and quietly conclude there is nothing to find.

    Module-level and duck-typed because the callers are not all looking at a
    'ShapeConfiguration' - a bill of materials walks whatever an assembly holds
    - and because two copies of this would be two answers to one question.
    """
    get_final_config = getattr(obj, "get_final_config", None)
    if get_final_config is None:
        return obj.config
    try:
        return get_final_config()
    except Exception as e:  # pylint: disable=broad-except
        pc_logging.debug("Failed to resolve the configuration of %s: %s" % (getattr(obj, "name", obj), e))
        return obj.config


class ShapeConfiguration:
    is_manufacturable: bool = False

    # The object-type parameters the type that produces this shape accepts,
    # mapped to their defaults (see 'PartFactory.ACCEPTED_OBJECT_TYPE_PARAMETERS',
    # which is what a part factory stamps here as the part is created). Empty
    # for every shape whose type contributes none - which today is every shape
    # that is not a part.
    object_type_parameters: dict = {}

    # The manufacturing tolerance this object's declaration stated, as a number,
    # or None if it stated none. Private because nothing may read it directly:
    # what a declaration wrote down is one of three answers to "how precisely is
    # this to be made", and 'get_tolerance()' is the one place that knows which
    # of them applies. Stamped on by the factory that created the object, like
    # the two below (see 'PartFactory._create_part').
    _tolerance: typing.Optional[float] = None

    # Whether the type that produces this shape takes a 'tolerance:' field at
    # all, and which file format's stated tolerance its file is to be read for.
    # Both are False/None for every type that does neither, which today is every
    # type but 'step' and the 'kicad' that inherits it.
    tolerance_field_accepted: bool = False
    tolerance_file_format: typing.Optional[str] = None

    # What the file turned out to say, once it has been read, and the sentinel
    # for "not read yet". A file is read at most once per object: it does not
    # change under a loaded package, and a STEP file large enough to be worth
    # caring about is large enough not to want scanned twice.
    _tolerance_from_file: typing.Any = _NOT_READ

    def __init__(self, config: dict) -> None:
        self.config = config

        if "name" in config:
            self.name = config["name"]
        else:
            name = "part" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.name = name
            self.config["name"] = name

        self.is_manufacturable = bool(config.get("manufacturable", True))

    @staticmethod
    def normalize(name, config):
        # Handle the case of the part being declared in the config
        # but not defined (a one liner like "part_name:").
        # TODO(clairbee): Revisit whether it's a bug or a feature
        #                 that this code allows to load undeclared scripts
        if config is None:
            config = {}

        # Instead of passing the name as a parameter,
        # enrich the configuration object
        # TODO(clairbee): reconsider passing the name as a parameter
        config["name"] = name
        config["orig_name"] = name

        return config

    def get_final_config(self) -> dict:
        """Return the final configuration (once all "alias" and "enrich" directives are resolved)."""
        return self.config

    def get_store_data(self) -> ShapeConfigStore:
        final_config = self.get_final_config()
        return ShapeConfigStore(final_config)

    async def get_mcftt(self, property: str):
        """Get the material, color, finish, texture or tolerance of the object."""

        store_data = self.get_store_data()

        if not store_data.is_purchasable and (
            "parameters" not in self.config or property not in self.config["parameters"]
        ):
            # shape = await self.get_wrapped()
            # TODO(clairbee): derive the property from the model

            if property == "finish":
                # By default, the finish is set to "none"
                value = "none"
            else:
                # By default, the parameter is not set
                value = None

            if value:
                if "parameters" not in self.config:
                    self.config["parameters"] = {}
                self.config["parameters"][property] = {
                    "type": "string",
                    "enum": [value],
                    "default": value,
                }
            else:
                kind = getattr(self, "kind", "object").capitalize()
                pc_logging.warning(f"{kind} '{self.name}' has no '{property}'")

            return value

        if (
            "parameters" not in self.config
            or property not in self.config["parameters"]
            or "default" not in self.config["parameters"][property]
        ):
            return None
        return self.config["parameters"][property]["default"]

    async def get_tolerance(self):
        """How precisely this object has to be made, or None if it cannot say.

        The one reader of the manufacturing tolerance. There are three places
        the answer can come from and they are not interchangeable, so nothing
        outside this reads any of them directly:

        1. The 'tolerance:' field of the declaration, for the types that take
           one. An author who wrote it down meant it, and it outranks the file:
           it is written precisely because the file did not say, and a file that
           later starts saying something else is a change to argue about rather
           than one to silently adopt.
        2. What the file itself states, for the types whose format can state it.
           A STEP file carrying GD&T already says how precisely each feature has
           to be made, in more detail than one number holds - so a file that
           tolerances several features differently answers NaN, which means
           "tolerated, feature by feature" and not "unknown". See
           'tolerance_inspect.reduce()'.
        3. The 'tolerance' object-type parameter, for the homogeneous types that
           accept it, which reads back as its type's default of 0.0 when nothing
           declared one.

        None is reserved for the object that has no way to answer at all: a type
        that takes neither the field nor the parameter, and whose file states
        nothing. It is not the same as 0.0, which is what "nobody said" reads as
        on a type that could have said - and the manufacturability test reports
        the two differently, because one is a declaration to fix and the other a
        part type to think again about.

        Asynchronous because of case 2, which reads a file, and because an
        object whose file is not there yet ('kicad' builds its STEP, a part with
        'fileFrom' downloads it) has to be free to answer without one.
        """
        if self._tolerance is not None:
            return self._tolerance

        stated = await self._get_file_tolerance()
        if stated is not None:
            return stated

        declared = self.get_object_type_parameter("tolerance")
        if declared is not None:
            return declared

        # A type that takes the field and whose file said nothing has said
        # nothing, which is 0.0 - the same "nobody said" the parameter's default
        # is, reached the other way.
        if self.tolerance_field_accepted:
            return 0.0
        return None

    async def _get_file_tolerance(self):
        """What this object's file states about its tolerance, read once."""
        if self.tolerance_file_format is None:
            return None
        if self._tolerance_from_file is not _NOT_READ:
            return self._tolerance_from_file

        path = getattr(self, "path", None)
        value = await asyncio.to_thread(tolerance_inspect.of_file, self.tolerance_file_format, path)
        # Only a file that was there gave an answer worth keeping. A 'kicad'
        # part's STEP file does not exist until the part is built, and
        # remembering the "nothing" read before that would outlive the reason
        # for it.
        if value is not None or (path and os.path.isfile(path)):
            self._tolerance_from_file = value
        return value

    def get_object_type_parameter(self, name: str):
        """The value of an object-type parameter, with the type's default applied.

        The counterpart of 'get_mcftt()' for the parameters a type contributes
        rather than the object invents. It reads the same place - the object's
        own 'parameters:' - and differs in what happens when nothing is
        declared: the default comes from the type that produces the shape, not
        from here.

        The default is applied *here*, on the way out, and is deliberately never
        written into 'config["parameters"]'. 'Shape.__init__' hashes that
        dictionary into the shape's cache key, so injecting a default would move
        the key of every homogeneous part that never mentioned a tolerance - a
        mass invalidation of existing cache entries for a value nobody set. Read
        this way, an undeclared tolerance stays out of the hash entirely, while a
        tolerance somebody did declare keys the cache like any other input,
        because it is one.

        The default doubles as the parameter's type witness: a numeric default
        means the parameter is numeric, so a declared value is coerced to a
        number. A value that will not coerce is reported and the default is used
        instead, which is how 'PartConfigManufacturing' treats a manufacturing
        method it does not recognize.

        Reads 'self.config' rather than the resolved final configuration, the
        same as 'get_mcftt()' does, so an alias reports what the alias itself
        declares. That is a pre-existing property of both readers, not something
        decided here.
        """
        accepted = self.object_type_parameters
        if name not in accepted:
            # Not a parameter this type contributes at all.
            return None
        default = accepted[name]
        fallback = None if isinstance(default, _NoDefault) else default

        parameters = self.config.get("parameters") or {}
        declared = parameters.get(name) if isinstance(parameters, dict) else None
        if not isinstance(declared, dict) or "default" not in declared:
            return fallback

        value = declared["default"]
        if isinstance(default, float):
            try:
                return float(value)
            except (TypeError, ValueError):
                kind = getattr(self, "kind", "object").capitalize()
                pc_logging.error(f"{kind} '{self.name}' has a non-numeric '{name}': {value!r}")
                return fallback
        return value
