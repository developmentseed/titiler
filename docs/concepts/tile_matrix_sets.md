
![](https://user-images.githubusercontent.com/10407788/98733872-30ae3f80-236f-11eb-9c98-6ecbc43f0756.png)

Slippy map tiles are square or rectangular images that follows a coordinates system define by a grid called `Tile Matrix`: http://docs.opengeospatial.org/is/17-083r2/17-083r2.html. The [`Web Mercator grid`](https://en.wikipedia.org/wiki/Web_Mercator_projection) is the **de facto standard** for Web maps. Made popular by google since 2005, it has pros and cons and:

> With any such projection, some distortion is unavoidable. In the Mercator projection, geographical features further from the equator are exaggerated in size. For example, Greenland appears to be of a similar size to Africa. However, Africa is actually more than 14 times as large (by area).

ref: https://developer.tomtom.com/blog/decoded/understanding-map-tile-grids-and-zoom-levels


As one of the first requirement, we built `TiTiler` with builtin support for serving tiles in multiple Projections by using [`rio-tiler`](https://github.com/cogeotiff/rio-tiler) and [`morecantile`](https://github.com/developmentseed/morecantile) which provide the low level TileMatrixSets support.

```python
r = requests.get("https://api.cogeo.xyz/tileMatrixSets").json()

print("Supported TMS:")
for tms in r["tileMatrixSets"]:
    print("-", tms["id"])

Supported TMS:
- CanadianNAD83_LCC
- EPSG3413
- EPSG6933
- EuropeanETRS89_LAEAQuad
- LINZAntarticaMapTilegrid
- NZTM2000
- UPSAntarcticWGS84Quad
- UPSArcticWGS84Quad
- UTM31WGS84Quad
- WebMercatorQuad
- WorldCRS84Quad
- WorldMercatorWGS84Quad
```

You can easily add more TileMatrixSet support, see [custom-tms](concepts/customization/#custom-tms).


Example: [Notebook](/examples/Working_with_nonWebMercatorTMS.ipynb)
