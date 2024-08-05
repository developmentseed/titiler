
![](https://user-images.githubusercontent.com/10407788/98733872-30ae3f80-236f-11eb-9c98-6ecbc43f0756.png)

Slippy map tiles are square or rectangular images that follow a coordinate system defined by a grid called `Tile Matrix`: http://docs.opengeospatial.org/is/17-083r2/17-083r2.html. The [`Web Mercator grid`](https://en.wikipedia.org/wiki/Web_Mercator_projection) is the **de facto standard** for Web maps. Made popular by google since 2005, it has pros and cons and:

> With any such projection, some distortion is unavoidable. In the Mercator projection, geographical features further from the equator are exaggerated in size. For example, Greenland appears to be of a similar size to Africa. However, Africa is actually more than 14 times as large (by area).

ref: https://developer.tomtom.com/blog/decoded/understanding-map-tile-grids-and-zoom-levels


As one of the first requirements, we built `TiTiler` with support for serving tiles in multiple Projections by using [`rio-tiler`](https://github.com/cogeotiff/rio-tiler) and [`morecantile`](https://github.com/developmentseed/morecantile) which provide the low level TileMatrixSets support.

```python
$ curl http://127.0.0.1:8000/tileMatrixSets | jq '.tileMatrixSets[] | .id'
"LINZAntarticaMapTilegrid"
"EuropeanETRS89_LAEAQuad"
"CanadianNAD83_LCC"
"UPSArcticWGS84Quad"
"NZTM2000"
"NZTM2000Quad"
"UTM31WGS84Quad"
"UPSAntarcticWGS84Quad"
"WorldMercatorWGS84Quad"
"WGS1984Quad"
"WorldCRS84Quad"
"WebMercatorQuad"
```

You can easily add more TileMatrixSet support, see [custom tms](advanced/customization.md#custom-tms).


Notebook: [Working_with_nonWebMercatorTMS](examples/notebooks/Working_with_nonWebMercatorTMS.ipynb)
