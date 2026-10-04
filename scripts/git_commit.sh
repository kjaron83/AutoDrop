#!/usr/bin/env bash

# We specify the script directory, regardless of where we started it from
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
CONFIG_FILE="$SCRIPT_DIR/.env_path"
USER_FILE="$SCRIPT_DIR/.git_user"
EMAIL_FILE="$SCRIPT_DIR/.git_email"

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

if [ -f "$USER_FILE" ]; then
    # Read the first line and trim the whitespace
    USER_NAME=$(head -n 1 "$USER_FILE" | xargs)
    echo "Using git user: $USER_NAME"
else
    echo "Error: Configuration file '$USER_FILE' not found."
    echo "Please create it in the same directory as this script."
    exit 1
fi

if [ -f "$EMAIL_FILE" ]; then
    # Read the first line and trim the whitespace
    EMAIL=$(head -n 1 "$EMAIL_FILE" | xargs)
    echo "Using git email $EMAIL"
else
    echo "Error: Configuration file '$EMAIL_FILE' not found."
    echo "Please create it in the same directory as this script."
    exit 1
fi

cd "$BASE_DIR"

export GIT_AUTHOR_NAME="$USER_NAME"
export GIT_AUTHOR_EMAIL="$EMAIL"
export GIT_COMMITTER_NAME="$USER_NAME"
export GIT_COMMITTER_EMAIL="$EMAIL"

set -e
git commit -m "$@"
