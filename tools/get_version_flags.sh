#!/bin/bash
# Generate --define flags for all game versions

function line() {
    for game_dir in maxbloks/*/; do
	game=$(basename "$game_dir")
	version=$(jq -r '.version' "$game_dir/version.json" 2>/dev/null || echo "0.0.0")
	echo -n "--define=${game}-version=${version} "
    done
}

l=$(line)
echo "build $l"
echo "test $l"

