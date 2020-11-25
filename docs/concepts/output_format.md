
`TiTiler` supports the common output format for map tiles: JPEG, PNG and WEBP.

While some format (e.g PNG) are able to encode Uint16 or Float datatypes, most web browser only supports 8 bytes data (meaning that it has to be between 0 and 255).
It's on the user to know what datatype is the input source (COG), and what kind of `post processing` there is to do to create a valid web map tile.

`TiTiler` has also support for more complex output data format, such as JPEG2000 or GeoTIFF. While it might not be useful for FrontEnd display (most broswer can't decode GeoTIFF natively), some user could want to transmit the data as `raw` values to some applications (non-web display).

Default output types/extensions are:

* `.tif`: image/tiff; application=geotiff
* `.jp2`: image/jp2
* `.png`: image/png
* `.pngraw`: image/png
* `.jpg`: image/jpeg
* `.webp`: image/webp
* `.npy`: application/x-binary

## NumpyTile

While `.tif` could be interesting, decoding the `GeoTIFF` format in requires non-native/default libraries. Recently, in colaboration with Planet, we started exploring the use of Python [`Numpy Format`](https://numpy.org/devdocs/reference/generated/numpy.lib.format.html#format-version-1-0) to encode the data array.

https://github.com/planetlabs/numpytiles-spec

> This specification attempts to create a standard for representing uncompressed, full bit-depth, raster imagery that can be easily communicated between a server and a client.

Example:

```python
import numpy
import requests
from io import BytesIO

url = "https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif"

r = requests.get("https://api.cogeo.xyz/cog/tiles/14/10818/9146.npy",
    params = {
        "url": url,
    }
)
data = numpy.load(BytesIO(r.content))
print(data.shape)
>>> (4, 256, 256)

# By default titiler will return a concatenated data,mask array.
data, mask = data[0:-1], data[-1]
```

See the notebook: [/examples/Working_with_NumpyTile.ipynb](/examples/Working_with_NumpyTile)

