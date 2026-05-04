# Releasing

Releases are automated via [release-please](https://github.com/googleapis/release-please-action). The process is driven entirely by [conventional commits](https://www.conventionalcommits.org/) merged to `main`.

## How it works

1. Every push to `main` triggers the `release-please` job in [`.github/workflows/release.yml`](.github/workflows/release.yml).
2. release-please opens (or updates) a release PR that:
   - Bumps the version in `pyproject.toml`, all sub-package `pyproject.toml` files, and `__init__.py` files
   - Bumps `appVersion` in `deployment/k8s/charts/Chart.yaml`
   - Updates `CHANGES.md` with the changelog for the new version
3. When that PR is merged, release-please creates a GitHub release tagged `X.Y.Z`, which triggers the PyPI publish workflow.

## Helm chart version

The Helm chart `version:` in `deployment/k8s/charts/Chart.yaml` is **not** managed by release-please. The chart version is bumped manually when chart structure changes (templates, values, dependencies). The `appVersion` field (the titiler app version the chart deploys) is still updated automatically alongside every Python release, and as part of this process, the chart version can be manually updated by bumping the version in a simple commit in the release please PR.

## Commit message convention

Version bumps follow [semantic versioning](https://semver.org/) based on commit type:

| Commit type | Version bump |
|-------------|-------------|
| `fix:` | patch |
| `feat:` | minor |
| `feat!:` or `BREAKING CHANGE:` footer | major |

## (Almost) No manual steps required

All version files are updated automatically. Do not manually edit version strings in `pyproject.toml`, `Chart.yaml` (`appVersion`), or `__init__.py` files — release-please owns those. The `version:` field in `Chart.yaml` is the only exception: bump it manually when chart structure changes warrant a new chart release.
