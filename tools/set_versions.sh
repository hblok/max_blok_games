#!/bin/bash
# Update game.json files with versions from version.json

set -e

for game_dir in maxbloks/*/; do
    version=$(jq -r '.version' "$game_dir/version.json" 2>/dev/null)
    [ -z "$version" ] && continue
    sed -i "s/{VERSION}/$version/g" "$game_dir/game.json"
done
