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

In GDAL 3.12, new environment variables might be introduced to enable more control over the VRT driver: https://github.com/OSGeo/gdal/pull/12669

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
