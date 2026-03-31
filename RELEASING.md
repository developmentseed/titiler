# Releasing

Releases are automated via [release-please](https://github.com/googleapis/release-please-action). The process is driven entirely by [conventional commits](https://www.conventionalcommits.org/) merged to `main`.

## How it works

1. Every push to `main` triggers the `release-please` job in [`.github/workflows/release.yml`](.github/workflows/release.yml).
2. release-please opens (or updates) a release PR that:
   - Bumps the version in `pyproject.toml`, all sub-package `pyproject.toml` files, and `__init__.py` files
   - Bumps `appVersion` in `deployment/k8s/charts/Chart.yaml`
   - Updates `CHANGES.md` with the changelog for the new version
3. When that PR is merged, release-please creates a GitHub release tagged `X.Y.Z`, which triggers the PyPI publish workflow.

## Helm chart releases

The Helm chart (`deployment/k8s/charts/`) is versioned independently from the Python package. release-please opens a separate helm release PR when commits touch files under `deployment/k8s/charts/`. That PR bumps `version:` in `Chart.yaml` and updates `deployment/k8s/charts/CHANGELOG.md`. The resulting GitHub release is tagged `helm-vX.Y.Z`.

**Commit messages matter for chart releases.** A chart version bump only happens when a commit both:
- touches at least one file under `deployment/k8s/charts/`, **and**
- uses a bump-triggering type (`fix:`, `feat:`, or a breaking change)

`chore:`, `ci:`, `docs:`, and other non-bumping types that touch chart files are valid conventional commits but will **not** produce a chart release. Use them for housekeeping that doesn't warrant a version bump (e.g. updating CI config, fixing a comment).

Examples:

```
fix(helm): correct resource limit defaults         → patch bump
feat(helm): add support for extra environment vars → minor bump
feat(helm)!: rename required value X to Y         → major bump
chore(helm): update maintainer list               → no bump
```

## Commit message convention

Version bumps follow [semantic versioning](https://semver.org/) based on commit type:

| Commit type | Version bump |
|-------------|-------------|
| `fix:` | patch |
| `feat:` | minor |
| `feat!:` or `BREAKING CHANGE:` footer | major |

## No manual steps required

All version files are updated automatically. Do not manually edit version strings in `pyproject.toml`, `Chart.yaml`, or `__init__.py` files — release-please owns those.
