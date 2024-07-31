
<p align="center">
  <img width="500" src="https://user-images.githubusercontent.com/10407788/204678594-2502b8e3-9b6e-428a-8525-200026859c00.png"/>
</p>

TiTiler's first goal is to create a lightweight but performant dynamic tile server... but what do we mean by this?

When you zoom/pan on a web map, you are visualizing either vector or raster data that is loaded by your web client (e.g Chrome). Vector Tiles are rendered **On the Fly**, meaning the map library (e.g MapboxGL) will apply styling on the vector it receives to create a visual representation on the map. This is possible because vector data can be encoded and compressed very efficiently and result in each tile being only couple of kilo octets.

On the other side, raster data is a really dense format, a `256 x 256 x 3` tile (True color image) needs to encode `196 608` values, and depending on the data type (Integer, Float, Complex), a raster tile can be really heavy. Depending on the dataset data type, some operations might be needed in order to obtain a visual representation (e.g. rescaling, colormap, ... ). Map library will almost only accept Uint8 RGB(A) tile encoded as PNG, JPEG or Webp.

## **Static tiling**

<p align="center">
  <img src="https://user-images.githubusercontent.com/10407788/204676883-d617d3bd-7ea2-4775-a7e9-f6b6afe1d801.png"/>
</p>

`Static` tiling is referring to `static` tiles (file on storage) that are pre-rendered from input dataset. Here are the steps needed to create those tiles:

* rescale the data to integer (0 -> 255), if datatype in not Uint8
* reproject the data to Web Mercator (or the projection of the web map application)
* split the data in tiles (256x256 or 512x512) and create different zoom levels (ref: https://gdal.org/programs/gdal2tiles.html)

When the tiles are available on a storage, you can either put a web server (e.g. [tilecache](http://www.tilecache.org), [mapserver](https://mapserver.org/fr/)) or maybe directly put a CDN, which will allow map client to `fetch` the tiles.

##### Pro

- Fast
- Relatively simple to create the tiles (`gdal2tiles.py`)

##### Cons

- You have to manage a lot of tiny files
- Choices are made for the user (projection, rescaling, ...)
- Some tiles might never been loaded

## **Dynamic tiling**

<p align="center">
  <img src="https://user-images.githubusercontent.com/10407788/204676918-6fabc35f-e617-47c0-ae63-912cd7d996d7.png"/>
</p>

The goal of the `Dynamic Tiling` process is to get rid of all the pre-processing steps, by creating a tile server which can access the raw data (COG) and apply operations (rescaling, reprojection, image encoding) to create the visual tiles **on the fly**.

* Open the file and get internal metadata (stored in the header of the file)
* Read internal parts needed to construct the output tile
* Apply data rescaling (if needed)
* Apply colormap (if needed)
* Encode the data into a visual image format (JPEG, PNG, WEBP)

##### Pro

- Access the raw data
- Multiple projection support
- User defined rescaling (when working with non-byte data)
- User defined Colormap
- Selection of bands/bands combination/bands math
- Apply custom processing on the tile data
- Dynamic mosaic with multiple datasets (user defined image order and pixel selection methods)

##### Cons

- Latency. Creating a tile from a COG means at least 2 GET requests (if web optimized).
- Dynamic tile server are more complex than Static tile server (which just serve files from a storage)
- No easy update (you need to re-write the whole COG)
- Tile server like TiTiler might present too many options (this is because titiler aim to support all COG types)


## Summary

With `Static` tile generation you are often limited because you are visualizing data that is fixed and stored somewhere on a disk. With `Dynamic tiling`, users have the possibility to apply their own choice of processing (e.g rescaling, masking) before creating the `image`.

Static tiling will always be faster than dynamic tiling, but a cache layer can be set up in front of the dynamic tiler, but using a dynamic tiler often means that same tile won't be serve twice (because users can set multiple options).

## Links
[https://medium.com/devseed/cog-talk-part-1-whats-new-941facbcd3d1](https://medium.com/devseed/cog-talk-part-1-whats-new-941facbcd3d1)

[https://kylebarron.dev/blog/cog-mosaic/overview](https://kylebarron.dev/blog/cog-mosaic/overview)

[https://mapdataservices.wordpress.com/2014/05/05/digital-mappings-dynamic-makeover/](https://mapdataservices.wordpress.com/2014/05/05/digital-mappings-dynamic-makeover/)

[https://medium.com/indigoag-eng/more-and-better-satellite-imagery-through-dynamic-tiling-60dcd7ce66ce](https://medium.com/indigoag-eng/more-and-better-satellite-imagery-through-dynamic-tiling-60dcd7ce66ce)

[https://sparkgeo.com/blog/terradactile-generate-cogs-from-aws-terrain-tiles/](https://sparkgeo.com/blog/terradactile-generate-cogs-from-aws-terrain-tiles/)

[https://www.azavea.com/blog/2019/04/23/using-cloud-optimized-geotiffs-cogs/](https://www.azavea.com/blog/2019/04/23/using-cloud-optimized-geotiffs-cogs/)

[https://hi.stamen.com/stamen-aws-lambda-tiler-blog-post-76fc1138a145](https://hi.stamen.com/stamen-aws-lambda-tiler-blog-post-76fc1138a145)
