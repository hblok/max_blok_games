#!/bin/bash
# Extract version from git tag
TAG=$(git describe --tags --always 2>/dev/null)

if [ -z "$TAG" ]; then
    VERSION_NAME="0.0.0-dev"
else
    VERSION_NAME="${TAG#v}"
fi

export RELEASE_VERSION=$(echo $VERSION_NAME | cut -f 1 -d '-')
export RELEASE_NAME=$(echo $VERSION_NAME | cut -f 2 -d '-')

