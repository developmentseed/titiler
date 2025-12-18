"""titiler.extensions"""

__version__ = "1.0.1"

from .cogeo import cogValidateExtension  # noqa
from .render import stacRenderExtension  # noqa
from .stac import stacExtension  # noqa
from .viewer import cogViewerExtension, stacViewerExtension  # noqa
from .wms import wmsExtension  # noqa
from .wmts import wmtsExtension  # noqa
