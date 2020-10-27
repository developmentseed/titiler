
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

* **layer_dependency**: Define band indexes or expression
    ```python
    @dataclass
    class BidxExprParams(DefaultDependency):
        """Band Indexes and Expression parameters."""

        bidx: Optional[str] = Query(
            None, title="Band indexes", description="comma (',') delimited band indexes",
        )
        expression: Optional[str] = Query(
            None,
            title="Band Math expression",
            description="rio-tiler's band math expression (e.g B1/B2)",
        )

        def __post_init__(self):
            """Post Init."""
            if self.bidx is not None:
                self.kwargs["indexes"] = tuple(
                    int(s) for s in re.findall(r"\d+", self.bidx)
                )

            if self.expression is not None:
                self.kwargs["expression"] = self.expression
    ```

* **dataset_dependency**: Overwride nodata value, apply rescaling or change default resampling.
    ```python
    @dataclass
    class DatasetParams(DefaultDependency):
        """Low level WarpedVRT Optional parameters."""

        nodata: Optional[Union[str, int, float]] = Query(
            None, title="Nodata value", description="Overwrite internal Nodata value"
        )
        unscale: Optional[bool] = Query(
            None,
            title="Apply internal Scale/Offset",
            description="Apply internal Scale/Offset",
        )
        resampling_method: ResamplingNames = Query(
            ResamplingNames.nearest, description="Resampling method."  # type: ignore
        )

        def __post_init__(self):
            """Post Init."""
            if self.nodata is not None:
                self.kwargs["nodata"] = (
                    numpy.nan if self.nodata == "nan" else float(self.nodata)
                )

            if self.unscale is not None:
                self.kwargs["unscale"] = self.unscale

            if self.resampling_method is not None:
                self.kwargs["resampling_method"] = self.resampling_method.name
    ```
* **render_dependency**: Image rendering options.
    ```python
    @dataclass
    class RenderParams(DefaultDependency):
        """Image Rendering options."""

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
        return_mask: bool = Query(True, description="Add mask to the output data.")
        colormap: Optional[Dict[int, Tuple[int, int, int, int]]] = field(init=False)

        def __post_init__(self):
            """Post Init."""
            self.colormap = cmap.get(self.color_map.value) if self.color_map else None
    ```

* **additional_dependency**: Default dependency, will be passed are `**kwargs` to all endpoints.

    ```python
    additional_dependency: Callable[..., Dict] = field(default=lambda: dict())
    ```

For `TilerFactory`:

* **metadata_dependency**: `rio_tiler.io.BaseReader.metadata()` methods options
    ```python
    @dataclass
    class MetadataParams(DefaultDependency):
        """Common Metadada parameters."""

        # Required params
        pmin: float = Query(2.0, description="Minimum percentile")
        pmax: float = Query(98.0, description="Maximum percentile")

        # Optional params
        max_size: Optional[int] = Query(
            None, description="Maximum image size to read onto."
        )
        histogram_bins: Optional[int] = Query(None, description="Histogram bins.")
        histogram_range: Optional[str] = Query(
            None, description="comma (',') delimited Min,Max histogram bounds"
        )
        bounds: Optional[str] = Query(
            None,
            descriptions="comma (',') delimited Bounding box coordinates from which to calculate image statistics.",
        )

        def __post_init__(self):
            """Post Init."""
            if self.max_size is not None:
                self.kwargs["max_size"] = self.max_size

            if self.bounds:
                self.kwargs["bounds"] = tuple(map(float, self.bounds.split(",")))

            hist_options = {}
            if self.histogram_bins:
                hist_options.update(dict(bins=self.histogram_bins))
            if self.histogram_range:
                hist_options.update(
                    dict(range=list(map(float, self.histogram_range.split(","))))
                )
            if hist_options:
                self.kwargs["hist_options"] = hist_options

    ```

* **img_dependency**: Used in Crop/Preview to define size of the output image.
    ```python
    @dataclass
    class ImageParams(DefaultDependency):
        """Common Preview/Crop parameters."""

        max_size: Optional[int] = Query(
            1024, description="Maximum image size to read onto."
        )
        height: Optional[int] = Query(None, description="Force output image height.")
        width: Optional[int] = Query(None, description="Force output image width.")

        def __post_init__(self):
            """Post Init."""
            if self.width and self.height:
                self.max_size = None

            if self.width is not None:
                self.kwargs["width"] = self.width

            if self.height is not None:
                self.kwargs["height"] = self.height

            if self.max_size is not None:
                self.kwargs["max_size"] = self.max_size
    ```
