"""titiler.extensions"""

__version__ = "0.24.0"

from .cogeo import cogValidateExtension  # noqa
from .render import stacRenderExtension  # noqa
from .stac import stacExtension  # noqa
from .viewer import cogViewerExtension, stacViewerExtension  # noqa
from .wms import wmsExtension  # noqa
