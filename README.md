# titiler

A lightweight Cloud Optimized GeoTIFF tile server.

# Deployment

**To Do**

# Test locally
```bash
$ uvicorn titiler.app:app --reload
```

### Docker
```
$ docker-compose build
$ docker-compose up 
```



## Authors
Created by [Development Seed](<http://developmentseed.org>)


## Contribution & Development

Issues and pull requests are more than welcome.

**dev install**

```bash
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler
$ pip install -e .[dev]
```

**Python3.6 only**

This repo is set to use `pre-commit` to run *flake8*, *pydocstring* and *black* ("uncompromising Python code formatter") when commiting new code.

```bash
$ pre-commit install
```
