
TiTiler first goal is to create lightweight but performante dynamic tile server... but what do we mean by this.

When you zoom/pan on a web map, you are visualizing either vector or raster data which are loaded by your web client (e.g Chrome). Vector Tiles are rendered `On the Fly`, meaning the map library (e.g MapgoxGL) will apply colors or width on the vector it receives to create a visual representation on the map. This is possible because we can encode and compress `vector` data very efficently, which each tile being only couple of kilo octets.

On the other side, raster data is a really dense format, a `256 x 256 x 3` tile (True color image) needs to encode `196 608` values, and depending on the data type (Integer, Float, Complex), a raster tile can be really heavy. Note, if the original data is stored in `Float`, to be able to obtain a visual representation we need to `rescale` the initial data to a `Byte` range of 0 to 255 values.

## Static tiling steps

Before, to be able to visualize a raster data on a web map, we need to:

* rescale the data to integer (0 -> 255)
* reproject the data to Web Mercator (or the projection of the web map application)
* split the data in tiles (256x256 or 512x512) and create different zoom levels (ref: https://gdal.org/programs/gdal2tiles.html)
* create a tile server which will read the tiles from a directoy/cloud storage


## Dynamic tiling steps

The goal of the `Dynamic Tiling` process is to get rid of all the pre-processing steps, by creating a tile server which can access the raw data (COG) and apply operations (rescaling, reprojection, image encoding) to create the visual tiles **on the fly**.

* Open the file and get internal metadata (stored in the header of the file)
* Read internal parts needed to construct the output tile
* Apply data rescaling (if needed)
* Apply colormap (if needed)
* Encode the data into a visual image format (JPEG, PNG, WEBP)

![](https://user-images.githubusercontent.com/10407788/98711823-7f4de080-2353-11eb-9c8a-8a46550651ae.png)


With `Static` tile generation you are often limited because you are visualizing a data that is fixed and stored somewhere on a disk. With `Dynamic tiling`, the user has the possibility to apply its own choice of processing (e.g rescaling, masking) before creating the `image`.

### Dynamic Tiling features

- Access the raw data
- Multiple projection support
- Rescaling (when working with non-byte data)
- Colormap
- Selection of bands/bands combination/bands math

## Links
[https://medium.com/devseed/cog-talk-part-1-whats-new-941facbcd3d1](https://medium.com/devseed/cog-talk-part-1-whats-new-941facbcd3d1)

[https://kylebarron.dev/blog/cog-mosaic/overview](https://kylebarron.dev/blog/cog-mosaic/overview)

[https://mapdataservices.wordpress.com/2014/05/05/digital-mappings-dynamic-makeover/](https://mapdataservices.wordpress.com/2014/05/05/digital-mappings-dynamic-makeover/)

[https://medium.com/indigoag-eng/more-and-better-satellite-imagery-through-dynamic-tiling-60dcd7ce66ce](https://medium.com/indigoag-eng/more-and-better-satellite-imagery-through-dynamic-tiling-60dcd7ce66ce)

[https://sparkgeo.com/blog/terradactile-generate-cogs-from-aws-terrain-tiles/](https://sparkgeo.com/blog/terradactile-generate-cogs-from-aws-terrain-tiles/)

[https://www.azavea.com/blog/2019/04/23/using-cloud-optimized-geotiffs-cogs/](https://www.azavea.com/blog/2019/04/23/using-cloud-optimized-geotiffs-cogs/)

[https://hi.stamen.com/stamen-aws-lambda-tiler-blog-post-76fc1138a145](https://hi.stamen.com/stamen-aws-lambda-tiler-blog-post-76fc1138a145)
