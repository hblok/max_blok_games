#!/bin/bash
# Update game.json files with versions from version.json

#set -e

for game_dir in maxbloks/*; do
    version_json="$game_dir/version.json"
    game_json="$game_dir/game.json"    
    [ -f "$version_json" ] || continue
    [ -f "$game_json" ] || continue
    
    version=$(jq -r '.version' "$version_json")
    [ -z "$version" ] && continue
    
    sed -i "s/{VERSION}/$version/g" $game_json
    
    echo "Wrote $version to $game_json"
done
