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

### Release

This is a checklist for releasing a new version of **titiler**.

1. Create a release branch named `release/vX.Y.Z`, where `X.Y.Z` is the new version

2. Make sure the [Changelog](CHANGES.md) is up to date with latest changes and release date set

3. Update `version: {chart_version}` (e.g: `version: 1.1.6 -> version: 1.1.7`) in `deployment/k8s/charts/Chart.yaml`

4. Run [`bump-my-version`](https://callowayproject.github.io/bump-my-version/) to update all titiler's module versions: `bump-my-version bump minor --new-version 0.20.0`

5. Push your release branch, create a PR, and get approval

6. Once the PR is merged, create a new (annotated, signed) tag on the appropriate commit. Name the tag `X.Y.Z`, and include `vX.Y.Z` as its annotation message

7. Push your tag to Github, which will kick off the publishing workflow

8. Create a [new release](https://github.com/developmentseed/titiler/releases/new) targeting the new tag, and use the "Generate release notes" feature to populate the description. Publish the release and mark it as the latest
