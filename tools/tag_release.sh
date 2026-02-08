#!/bin/bash
# Tag and release a game

set -e

game=$1
[ -z "$game" ] && echo "Usage: $0 <game>" && exit 1

python3 tools/increment_version.py "$game"
version=$(jq -r '.version' "maxbloks/$game/version.json")
git commit -m "Release: $game $version" "maxbloks/$game/version.json"
tag="v${version}-${game}"
git tag $tag
git push origin main && git push origin $tag
