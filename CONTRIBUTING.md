# Development - Contributing

Issues and pull requests are more than welcome: https://github.com/developmentseed/titiler/issues

**dev install**

```bash
git clone https://github.com/developmentseed/titiler.git
cd titiler

python -m pip install \
   pre-commit \
   -e src/titiler/core["test"] \
   -e src/titiler/extensions["test,cogeo,stac"] \
   -e src/titiler/mosaic["test"] \
   -e src/titiler/application["test"]
```

**pre-commit**

This repo is set to use `pre-commit` to run *isort*, *flake8*, *pydocstring*, *black* ("uncompromising Python code formatter") and mypy when committing new code.

```bash
pre-commit install
```

### Run tests

Each `titiler`'s modules has its own test suite which can be ran independently

```
# titiler.core
python -m pytest src/titiler/core --cov=titiler.core --cov-report=xml --cov-append --cov-report=term-missing

# titiler.extensions
python -m pytest src/titiler/extensions --cov=titiler.extensions --cov-report=xml --cov-append --cov-report=term-missing

# titiler.mosaic
python -m pytest src/titiler/mosaic --cov=titiler.mosaic --cov-report=xml --cov-append --cov-report=term-missing

# titiler.application
python -m pytest src/titiler/application --cov=titiler.application --cov-report=xml --cov-append --cov-report=term-missing
```

### Docs

```bash
git clone https://github.com/developmentseed/titiler.git
cd titiler
python -m pip install -r requirements/requirements-docs.txt
```

Hot-reloading docs:

```bash
mkdocs serve -f docs/mkdocs.yml
```

To manually deploy docs (note you should never need to do this because Github
Actions deploys automatically for new commits.):

```bash
mkdocs gh-deploy -f docs/mkdocs.yml
```
