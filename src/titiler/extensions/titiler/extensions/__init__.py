"""titiler.extensions"""

__version__ = "0.11.0"

from .cogeo import cogValidateExtension  # noqa
from .gdal_wmts import gdalwmtsExtension  # noqa
from .stac import stacExtension  # noqa
from .viewer import cogViewerExtension, stacViewerExtension  # noqa
from .wms import wmsExtension  # noqa
