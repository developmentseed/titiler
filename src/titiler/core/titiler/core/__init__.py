"""titiler.core"""

__version__ = "2.0.2"  # x-release-please-version

from . import dependencies, errors, factory, routing  # noqa
from .factory import (  # noqa
    AlgorithmFactory,
    BaseFactory,
    ColorMapFactory,
    MultiBaseTilerFactory,
    TilerFactory,
    TMSFactory,
)
