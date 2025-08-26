# Releasing

This is a checklist for releasing a new version of **titiler**.

1. Determine the next version

   We currently do not have published versioning guidelines. We usually use `minor` version update when pushing breaking changes and `patch` for every other updates

2. Create a release branch named `release/vX.Y.Z`, where `X.Y.Z` is the new version
3. Search and replace all instances of the current version number with the new version

   We recommend to use [`bump-my-version`](https://github.com/callowayproject/bump-my-version) CLI
   ```
   bump-my-version bump --new-version 3.1.0
   ```

4. Manually increase the helm chart `version` in `/deployment/k8s/charts/Chart.yaml (not matching titiler's version)
5. Update [CHANGES.md](./CHANGES.md) for the new version
6. Push your release branch, create a PR, and get approval
7. Once the PR is merged, create a new (annotated, signed) tag on the appropriate commit

   Name the tag `X.Y.Z`, and include `vX.Y.Z` as its annotation message

8. Push your tag to Github, which will kick off the publishing workflow
9. Create a [new release](https://github.com/developmentseed/titiler/releases/new) targeting the new tag, and use the "Generate release notes" feature to populate the description.

   Publish the release and mark it as the latest.
