
`TiTiler` supports the common output format for map tiles: JPEG, PNG and WEBP.

While some formats (e.g PNG) are able to encode Uint16 or Float datatypes, most web browsers only supports 8 bit data (meaning that it has to be between 0 and 255).
It's on the user to know what datatype is the input source (COG), and what kind of `post processing` there is to do to create a valid web map tile.

`TiTiler` also has support for more complex output data formats, such as JPEG2000 or GeoTIFF. While it might not be useful for FrontEnd display (most browsers can't decode GeoTIFF natively), some users could want to transmit the data as `raw` values to some applications (non-web display).

Default output types/extensions are:

* `.tif`: image/tiff; application=geotiff
* `.jp2`: image/jp2
* `.png`: image/png
* `.pngraw`: image/png
* `.jpeg`: image/jpeg
* `.jpg`: image/jpg
* `.webp`: image/webp
* `.npy`: application/x-binary

## NumpyTile

While `.tif` could be interesting, decoding the `GeoTIFF` format requires non-native/default libraries. Recently, in collaboration with Planet, we started exploring the use of a [`Numpy-native format`](https://numpy.org/devdocs/reference/generated/numpy.lib.format.html#format-version-1-0) to encode the data array.

https://github.com/planetlabs/numpytiles-spec

> This specification attempts to create a standard for representing uncompressed, full bit-depth, raster imagery that can be easily communicated between a server and a client.

Example:

```python
import numpy
import requests
from io import BytesIO

url = "https://opendata.digitalglobe.com/events/mauritius-oil-spill/post-event/2020-08-12/105001001F1B5B00/105001001F1B5B00.tif"

r = requests.get("http://127.0.0.1:8000/cog/tiles/14/10818/9146.npy",
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

Notebook: [Working_with_NumpyTile](examples/notebooks/Working_with_NumpyTile.ipynb)

## JSONResponse

Sometimes rio-tiler's responses can contain `NaN`, `Infinity` or `-Infinity` values (e.g for Nodata). Sadly there is no proper ways to encode those values in JSON or at least not all web client supports it.

In  order to allow TiTiler to return valid responses we added a custom `JSONResponse` in `v0.3.10` which will automatically translate `float('nan')`, `float('inf')` and `float('-inf')` to `null` and thus avoid in valid JSON response.

```python

from fastapi import FastAPI
from titiler.core.resources.responses import JSONResponse

app = FastAPI(default_response_class=JSONResponse,)

@app.get("/something")
def return_something():
    return float('nan')
```

This `JSONResponse` is used by default in `titiler` Tiler Factories where `NaN` are expected (`info`, `statistics` and `point` endpoints).
