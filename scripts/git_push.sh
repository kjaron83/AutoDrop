#!/usr/bin/env bash

# We specify the script directory, regardless of where we started it from
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
CONFIG_FILE="$SCRIPT_DIR/.env_path"

# Check if the file exists next to the script
if [ -f "$CONFIG_FILE" ]; then
    # Read the first line and trim the whitespace
    BASE_DIR=$(head -n 1 "$CONFIG_FILE" | xargs)
    echo "Using base directory: $BASE_DIR"
else
    echo "Error: Configuration file '$CONFIG_FILE' not found."
    echo "Please create it in the same directory as this script."
    exit 1
fi

cd "$BASE_DIR"

set -e

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$CURRENT_BRANCH" = "master" ]; then
    echo "Error: Direct push to 'master' is forbidden."
    exit 1
fi

if [ $# -eq 0 ]; then
    echo "Pushing current branch '$CURRENT_BRANCH' to origin..."
    git push -u origin "$CURRENT_BRANCH"
else
    echo "Pushing branch '$@' to origin..."
    git push "$@"
fi
