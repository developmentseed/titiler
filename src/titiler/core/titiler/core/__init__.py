"""titiler.core"""

__version__ = "2.0.0dev0"

from . import dependencies, errors, factory, routing  # noqa
from .factory import (  # noqa
    AlgorithmFactory,
    BaseFactory,
    ColorMapFactory,
    MultiBaseTilerFactory,
    TilerFactory,
    TMSFactory,
)
