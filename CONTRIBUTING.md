# Development - Contributing

Issues and pull requests are more than welcome: https://github.com/developmentseed/titiler/issues

We recommand using [`uv`](https://docs.astral.sh/uv) as project manager for development.

See https://docs.astral.sh/uv/getting-started/installation/ for installation 

**dev install**

```bash
git clone https://github.com/developmentseed/titiler.git
cd titiler

# Install the package in editable mode, plus the "dev" dependency group.
# You can add `--group` arguments to add more groups, e.g. `--group notebook`.
uv sync
```

**pre-commit**

This repo is set to use `pre-commit` to run *isort*, *ruff* (linting and formatting), *mypy*, *zizmor* (GitHub Actions security audit), and *commitizen* (commit message linting) when committing new code.

```bash
uv run pre-commit install

# If needed, you can run pre-commit script manually
uv run pre-commit run --all-files
```

### Conventional Commits

This repo enforces [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
Commit messages must follow the format:

```
<type>[optional scope]: <description>
```

Common types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`.

The `commitizen` pre-commit hook (installed in the `commit-msg` stage via `uv run pre-commit install`) validates each commit message locally. The same check runs in CI via the `Commitlint` GitHub Actions workflow on every push.

Release notes and version bumps are generated automatically from conventional commit history using [Release Please](https://github.com/googleapis/release-please).

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
