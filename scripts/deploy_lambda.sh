#!/usr/bin/env bash

SUBPACKAGE_DIRS=(
    "core"
    "mosaic"
    "application"
)

for PACKAGE_DIR in "${SUBPACKAGE_DIRS[@]}"
do
    pushd ./titiler/${PACKAGE_DIR}
    rm -rf dist
    python setup.py sdist
    cp dist/*.tar.gz ../../deployment/aws/
    popd
done

cd deployment/aws && npm run cdk deploy titiler-phil-lambda-dev --verbose