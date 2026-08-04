# Security Policy

## Reporting a Vulnerability

If you find any vulnerabilities in `titiler`, don't hesitate to _report them_.

1. Use GitHub's security reporting tools.

see https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability#privately-reporting-a-security-vulnerability

2. Describe the vulnerability.

   If you have a fix, that is most welcome -- please attach or summarize it in your message!

3. We will evaluate the vulnerability and, if necessary, release a fix or mitigating steps to address it. We will contact you to let you know the outcome, and will credit you in the report.

   Please **do not disclose the vulnerability publicly** until a fix is released!

4. Once we have either a) published a fix, or b) declined to address the vulnerability for whatever reason, you are free to publicly disclose it.


## GDAL

`TiTiler` is built on top of Rasterio which is a python wrapper for the [GDAL](https://gdal.org/en/stable/) C++ library. At the time of writing, GDAL is responsible for most of the I/O and thus is where vulnerabilities could be harmful. For any `I/O` issues please first check [GDAL documentation](https://gdal.org/en/stable/user/security.html#security-considerations).

#### GDAL VRT Driver

There is a known security vulnerability with the VRT Driver:

> It can be used to access any valid GDAL dataset. If a hostile party, with knowledge of the location on the filesystem of a valid GDAL dataset, convinces a user to run gdal_translate a VRT file and give it back the result, it might be able to steal data. That could potentially be able for a web service accepting data from the user, converting it, and sending back the result.

see https://gdal.org/en/stable/user/security.html#gdal-vrt-driver

Thus we recommend deploying titiler in infrastructure with limited access to the filesystem. Users can also `disable` the VRT driver completely by using `GDAL_SKIP=VRT` environment variable.

GDAL 3.12 added two configuration options for finer control over the VRT driver, which are useful when `GDAL_SKIP=VRT` is too blunt because VRT is part of your product:

- `GDAL_VRT_ENABLE_RAWRASTERBAND` (default `YES`). Set it to `NO` to disable `VRTRawRasterBand` entirely.
- `GDAL_VRT_RAWRASTERBAND_ALLOWED_SOURCE` (default `SIBLING_OR_CHILD_OF_VRT_PATH`). Restricts which `SourceFilename` values a raw band may reference. The other values are `ONLY_REMOTE`, `ALL`, and an explicit path prefix.

The default is already restrictive, so running GDAL 3.12 or later closes most of this path without any configuration. Setting both options explicitly is still worth doing, because it survives a base image bump that changes the defaults.

GDAL 3.13.2 also restricts the `/vsicurl/` `header_file` option, which could otherwise be pointed at an arbitrary local file. The filename now defaults to being under `/vsimem/`, `/tmp`, or `TEMP`, and `CPL_VSIL_CURL_HEADER_FILE_KVP_ENABLED` controls the policy.

see https://gdal.org/en/stable/drivers/raster/vrt.html and https://gdal.org/en/stable/user/virtual_file_systems.html

#### Limit source's host

If users want to limit the sources that the application can access, they can also create custom `path_dependency` such as this one which limits valid sources to a list of known hosts:

```python
from urllib.parse import urlparse

from typing import Annotated
from titiler.core.factory import TilerFactory
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from fastapi import FastAPI, Query, HTTPException

# List of known host where dataset can be read from
known_host = [
   "devseed.org",
]

def DatasetPathParams(url: Annotated[str, Query(description="Dataset URL")]) -> str:
   """Create dataset path from args"""
   # validate Dataset host
   parsed = urlparse(url)
   if parsed.netloc not in known_host:
      raise HTTPException(
         status_code=400,
         detail="Nope, this is not a valid File - Please Try Again",
      )

   return url


app = FastAPI(title="My simple app")
app.include_router(TilerFactory(path_dependency=DatasetPathParams).router)

add_exception_handlers(app, DEFAULT_STATUS_CODES)
```

## Band math

The `expression` parameter is evaluated by rio-tiler through `numexpr`. rio-tiler validates expressions against an allowlist before evaluating them, and that validation was hardened in 9.1.0, so keep rio-tiler current.

Applications that only need band selection can remove the parameter altogether by passing a `layer_dependency` that omits it. `BidxParams` provides `bidx` without `expression`:

```python
from titiler.core.factory import TilerFactory
from titiler.core.dependencies import BidxParams
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from fastapi import FastAPI

app = FastAPI(title="My simple app")

# BidxExprParams (the default) provides both `bidx` and `expression`.
# BidxParams provides `bidx` only, so `expression` is not part of the API.
app.include_router(TilerFactory(layer_dependency=BidxParams).router)

add_exception_handlers(app, DEFAULT_STATUS_CODES)
```

The parameter then disappears from the OpenAPI schema and the endpoints reject it, which is a stronger guarantee than relying on validation.
