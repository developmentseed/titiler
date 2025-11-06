# Development - Contributing

Issues and pull requests are more than welcome: https://github.com/developmentseed/titiler/issues

We recommand using [`uv`](https://docs.astral.sh/uv) as project manager for development.

See https://docs.astral.sh/uv/getting-started/installation/ for installation 

**dev install**

```bash
git clone https://github.com/developmentseed/titiler.git
cd titiler
uv sync --dev
```

**pre-commit**

This repo is set to use `pre-commit` to run *isort*, *flake8*, *pydocstring*, *black* ("uncompromising Python code formatter") and mypy when committing new code.

```bash
uv run pre-commit install

# If needed, you can run pre-commit script manually 
uv run pre-commit run --all-files 
```

### Run tests

Each `titiler`'s modules has its own test suite which can be ran independently

```
# titiler.core
uv run pytest src/titiler/core --cov=titiler.core --cov-report=xml --cov-append --cov-report=term-missing

# titiler.extensions
uv run pytest src/titiler/extensions --cov=titiler.extensions --cov-report=xml --cov-append --cov-report=term-missing

# titiler.mosaic
uv run pytest src/titiler/mosaic --cov=titiler.mosaic --cov-report=xml --cov-append --cov-report=term-missing

# titiler.xarray
uv run pytest src/titiler/xarray --cov=titiler.xarray --cov-report=xml --cov-append --cov-report=term-missing

# titiler.application
uv run pytest src/titiler/application --cov=titiler.application --cov-report=xml --cov-append --cov-report=term-missing
```

### Docs

```bash
git clone https://github.com/developmentseed/titiler.git
cd titiler

# Build docs
uv run --group docs mkdocs build -f docs/mkdocs.yml
```

Hot-reloading docs:

```bash
uv run --group docs mkdocs serve -f docs/mkdocs.yml --livereload
```

To manually deploy docs (note you should never need to do this because Github
Actions deploys automatically for new commits.):

```bash
uv run --group docs mkdocs gh-deploy -f docs/mkdocs.yml
```