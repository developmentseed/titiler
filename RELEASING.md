# Releasing

This is a checklist for releasing a new version of **titiler**.

1. Create a release branch named `release/vX.Y.Z`, where `X.Y.Z` is the new version

2. Make sure the [Changelog](CHANGES.md) is up to date with latest changes and release date set

3. Update `version: {chart_version}` (e.g: `version: 1.1.6 -> version: 1.1.7`) in `deployment/k8s/charts/Chart.yaml`

4. Run [`bump-my-version`](https://callowayproject.github.io/bump-my-version/) to update all titiler's module versions: `uv run bump-my-version bump minor --new-version 0.20.0`

5. Push your release branch, create a PR, and get approval

6. Once the PR is merged, create a new (annotated, signed) tag on the appropriate commit. Name the tag `X.Y.Z`, and include `vX.Y.Z` as its annotation message

7. Push your tag to Github, which will kick off the publishing workflow

8. Create a [new release](https://github.com/developmentseed/titiler/releases/new) targeting the new tag, and use the "Generate release notes" feature to populate the description. Publish the release and mark it as the latest
