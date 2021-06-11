#!/usr/bin/env bash

set -Eeuo pipefail
# set -x # print each command before exe

DEPLOY_ENV=${1:-dev}

SUBPACKAGE_DIRS=(
    "core"
    "mosaic"
    "application"
)

for PACKAGE_DIR in "${SUBPACKAGE_DIRS[@]}"
do
    pushd "./titiler/${PACKAGE_DIR}"
    rm -rf dist
    python setup.py sdist
    cp dist/*.tar.gz ../../deployment/aws/
    popd
done

cd deployment/aws
cp ".env.${DEPLOY_ENV}" .env

npm run cdk deploy "dynamic-tiler-lambda-${DEPLOY_ENV}"