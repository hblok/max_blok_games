#!/bin/bash
# Update game.json files with versions from version.json

set -e

for game_dir in maxbloks/*; do
    version=$(jq -r '.version' "$game_dir/version.json")
    [ -z "$version" ] && continue
    game_json="$game_dir/game.json"
    sed -i "s/{VERSION}/$version/g" $game_json
    echo "Wrote $version to $game_json"
done

