# Development - Contributing

Issues and pull requests are more than welcome: https://github.com/developmentseed/titiler/issues

**dev install**

```bash
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler
$ pip install \
   pre-commit \
   -e src/titiler/core["test"] \
   -e src/titiler/extensions["test,cogeo,stac"] \
   -e src/titiler/mosaic["test"] \
   -e src/titiler/application["test"]
```

**pre-commit**

This repo is set to use `pre-commit` to run *isort*, *flake8*, *pydocstring*, *black* ("uncompromising Python code formatter") and mypy when committing new code.

```bash
$ pre-commit install
```

### Docs

```bash
$ git clone https://github.com/developmentseed/titiler.git
$ cd titiler
$ pip install nbconvert mkdocs mkdocs-material mkdocs-jupyter pygments pdocs
```

Hot-reloading docs:

```bash
$ mkdocs serve -f docs/mkdocs.yml
```

To manually deploy docs (note you should never need to do this because Github
Actions deploys automatically for new commits.):

```bash
$ mkdocs gh-deploy -f docs/mkdocs.yml
```

```bash
   pdocs as_markdown \
   --output_dir docs/src/api \
   --exclude_source \
   --overwrite \
   titiler.core.dependencies \
   titiler.core.factory \
   titiler.core.utils \
   titiler.core.routing \
   titiler.core.errors \
   titiler.core.resources.enums \
   titiler.core.middleware

   pdocs as_markdown \
   --output_dir docs/src/api \
   --exclude_source \
   --overwrite \
   titiler.extensions.cogeo \
   titiler.extensions.viewer \
   titiler.extensions.stac

   pdocs as_markdown \
   --output_dir docs/src/api \
   --exclude_source \
   --overwrite \
   titiler.mosaic.factory \
   titiler.mosaic.resources.enums \
   titiler.mosaic.errors
```
