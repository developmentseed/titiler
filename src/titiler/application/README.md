## titiler.application

<img style="max-width:400px" src="https://user-images.githubusercontent.com/10407788/115224800-53d9d980-a0db-11eb-86c3-1c94fde3ed4a.png"/>
<p align="center">Titiler's demo package.</p>

## Installation

```bash
$ pip install -U pip

# From Pypi
$ pip install titiler.application

# Or from sources
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler && pip install -e titiler/application
```

Launch Application
```bash
$ pip install uvicorn
$ uvicorn titiler.application.main:app --reload
```

## Package structure

```
titiler/
 └── application/
    ├── tests/                   - Tests suite
    └── titiler/application/     - `application` namespace package
        ├── routers/
        |   ├── cog.py           - Cloud Optimized `/cog` endpoints
        |   ├── mosaic.py        - mosaic `/mosaicjson` endpoints
        |   ├── stac.py          - STAC `/stac` endpoints
        |   └── tms.py           - TileMatrixSet endpoints
        ├── templates/
        |   ├── index.html       - demo landing page
        |   ├── cog_index.html   - demo viewer for `/cog`
        |   └── stac_index.html  - demo viewer for `/stac`
        ├── custom.py            - Titiler customisation (TMS, colormap...)
        ├── main.py              - Main FastAPI application
        ├── middleware.py        - Titiler custom middlewares
        ├── settings.py          - demo settings (cache, cors...)
        └── version.py           - version
```
