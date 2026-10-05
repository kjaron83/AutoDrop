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

LOCALES_DIR="autodrop/locales"
POT_FILE="$LOCALES_DIR/messages.pot"
CFG_FILE="babel.cfg"
PYBABEL="./env/bin/pybabel"

if [ ! -f "$PYBABEL" ]; then
    echo "Error: pybabel not found at $PYBABEL"
    exit 1
fi

mkdir -p "$LOCALES_DIR"

echo "Extracting translatable strings to $POT_FILE..."
$PYBABEL extract -F "$CFG_FILE" -o "$POT_FILE" .

echo "Updating translation catalogs in $LOCALES_DIR..."
$PYBABEL update -i "$POT_FILE" -d "$LOCALES_DIR"

echo "Translation catalogs updated successfully."
