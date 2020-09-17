
If you are new the concept of **Dependency Injection**, please checkout this awesome tutorial: https://fastapi.tiangolo.com/tutorial/dependencies/

In titiler `Factories`, we use the dependencies to define the inputs for each endpoints (and thus the OpenAPI documention).

Example:
```python
@dataclass
class ImageParams:
    """Common Image parameters."""

    max_size: Optional[int] = Query(
        1024, description="Maximum image size to read onto."
    )
    height: Optional[int] = Query(None, description="Force output image height.")
    width: Optional[int] = Query(None, description="Force output image width.")

    def __post_init__(self):
        """Post Init."""
        super().__post_init__()

        if self.width and self.height:
            self.max_size = None


@router.get(r"/preview.png")
def preview(
    url: str = Query(..., description="data set URL"), params: ImageParams = Depends(),
):

    with COGReader(url) as cog:
        data, mask = cog.preview(
            max_size=params.max_size,
            width=params.width,
            height=params.height,
        )
```

The `factories` allow users to set multiple default dependencies. Here is the list of common dependencies and their default values:

* **path_dependency**: Set dataset path (url).
    ```python
    @dataclass
    class PathParams(DefaultDependency):
        """Create dataset path from args"""

        url: str = Query(..., description="Dataset URL")

        # Placeholder
        # Factory can accept a reader defined in the PathParams.
        # This is for case where a user would want to indicate in the input url what
        # reader to use:
        # landsat+{landsat scene id}
        # sentinel+{sentinel scene id}
        # ...
        reader: Optional[Type[BaseReader]] = field(init=False, default=None)
    ```

* **tiles_dependency**
    ```python
    @dataclass
    class CommonParams(DefaultDependency):
        """Common Reader params."""

        bidx: Optional[str] = Query(
            None, title="Band indexes", description="comma (',') delimited band indexes",
        )
        nodata: Optional[Union[str, int, float]] = Query(
            None, title="Nodata value", description="Overwrite internal Nodata value"
        )
        resampling_method: ResamplingNames = Query(
            ResamplingNames.nearest, description="Resampling method."  # type: ignore
        )

        def __post_init__(self):
            """Post Init."""
            self.indexes = (
                tuple(int(s) for s in re.findall(r"\d+", self.bidx)) if self.bidx else None
            )
            if self.nodata is not None:
                self.nodata = numpy.nan if self.nodata == "nan" else float(self.nodata)

    @dataclass
    class TileParams(CommonParams):
        """Common Tile parameters."""

        expression: Optional[str] = Query(
            None,
            title="Band Math expression",
            description="rio-tiler's band math expression (e.g B1/B2)",
        )
        rescale: Optional[str] = Query(
            None,
            title="Min/Max data Rescaling",
            description="comma (',') delimited Min,Max bounds",
        )
        color_formula: Optional[str] = Query(
            None,
            title="Color Formula",
            description="rio-color formula (info: https://github.com/mapbox/rio-color)",
        )
        color_map: Optional[ColorMapNames] = Query(
            None, description="rio-tiler's colormap name"
        )
        colormap: Optional[Dict[int, Tuple[int, int, int, int]]] = field(init=False)

        def __post_init__(self):
            """Post Init."""
            super().__post_init__()

            self.colormap = cmap.get(self.color_map.value) if self.color_map else None
    ```


* **point_dependency**: Set band indexes or expression and allow overriding of the nodata value.
    ```python
    @dataclass
    class PointParams(DefaultDependency):
        """Point Parameters."""

        bidx: Optional[str] = Query(
            None, title="Band indexes", description="comma (',') delimited band indexes",
        )
        nodata: Optional[Union[str, int, float]] = Query(
            None, title="Nodata value", description="Overwrite internal Nodata value"
        )
        expression: Optional[str] = Query(
            None,
            title="Band Math expression",
            description="rio-tiler's band math expression (e.g B1/B2)",
        )

        def __post_init__(self):
            """Post Init."""
            self.indexes = (
                tuple(int(s) for s in re.findall(r"\d+", self.bidx)) if self.bidx else None
            )
            if self.nodata is not None:
                self.nodata = numpy.nan if self.nodata == "nan" else float(self.nodata)
    ```

* **tms_dependency**: The TMS dependency set the available TMS for a tile endpoint.
    ```python
    # Allow all morecantile TMS
    def TMSParams(
        TileMatrixSetId: TileMatrixSetNames = Query(
            TileMatrixSetNames.WebMercatorQuad,  # type: ignore
            description="TileMatrixSet Name (default: 'WebMercatorQuad')",
        )
    ) -> morecantile.TileMatrixSet:
        """TileMatrixSet Dependency."""
        return morecantile.tms.get(TileMatrixSetId.name)

    # or
    # Restrict the TMS to `WebMercatorQuad` only
    def WebMercatorTMSParams(
        TileMatrixSetId: WebMercatorTileMatrixSetName = Query(
            WebMercatorTileMatrixSetName.WebMercatorQuad,  # type: ignore
            description="TileMatrixSet Name (default: 'WebMercatorQuad')",
        )
    ) -> morecantile.TileMatrixSet:
        """TileMatrixSet Dependency."""
        return morecantile.tms.get(TileMatrixSetId.name)
    ```

* **additional_dependency**: Default dependency, will be passed are `**options.kwargs` to all reader methods.

    ```python
    @dataclass
    class DefaultDependency:
        """Dependency Base Class"""

        kwargs: dict = field(init=False, default_factory=dict)
    ```

For `TMSTilerFactory` and `TilerFactory`
* **metadata_dependency**: `rio_tiler.io.BaseReader.metadata()` methods options
```python
@dataclass
class MetadataParams(CommonParams):
    """Common Metadada parameters."""

    pmin: float = Query(2.0, description="Minimum percentile")
    pmax: float = Query(98.0, description="Maximum percentile")
    max_size: int = Query(1024, description="Maximum image size to read onto.")
    histogram_bins: Optional[int] = Query(None, description="Histogram bins.")
    histogram_range: Optional[str] = Query(
        None, description="comma (',') delimited Min,Max histogram bounds"
    )
    bounds: Optional[str] = Query(
        None,
        descriptions="comma (',') delimited Bounding box coordinates from which to calculate image statistics.",
    )
    hist_options: dict = field(init=False, default_factory=dict)

    def __post_init__(self):
        """Post Init."""
        super().__post_init__()

        if self.histogram_bins:
            self.hist_options.update(dict(bins=self.histogram_bins))
        if self.histogram_range:
            self.hist_options.update(
                dict(range=list(map(float, self.histogram_range.split(","))))
            )
        if self.bounds:
            self.bounds = tuple(map(float, self.bounds.split(",")))
```

* **img_dependency**:
```python
@dataclass
class ImageParams(TileParams):
    """Common Image parameters."""

    max_size: Optional[int] = Query(
        1024, description="Maximum image size to read onto."
    )
    height: Optional[int] = Query(None, description="Force output image height.")
    width: Optional[int] = Query(None, description="Force output image width.")

    def __post_init__(self):
        """Post Init."""
        super().__post_init__()

        if self.width and self.height:
            self.max_size = None
```
