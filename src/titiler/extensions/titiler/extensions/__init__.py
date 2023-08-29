"""titiler.extensions"""

__version__ = "0.13.3"

from .cogeo import cogValidateExtension  # noqa
from .stac import stacExtension  # noqa
from .viewer import cogViewerExtension, stacViewerExtension  # noqa
from .wms import wmsExtension  # noqa
