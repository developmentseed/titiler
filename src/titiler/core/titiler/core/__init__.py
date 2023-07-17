"""titiler.core"""

__version__ = "0.12.0"

from . import dependencies, errors, factory, routing  # noqa
from .factory import (  # noqa
    BaseTilerFactory,
    MultiBandTilerFactory,
    MultiBaseTilerFactory,
    TilerFactory,
)
