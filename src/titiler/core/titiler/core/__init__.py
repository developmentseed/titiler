"""titiler.core"""

__version__ = "1.1.1"

from . import dependencies, errors, factory, routing  # noqa
from .factory import (  # noqa
    AlgorithmFactory,
    BaseFactory,
    ColorMapFactory,
    MultiBaseTilerFactory,
    TilerFactory,
    TMSFactory,
)
