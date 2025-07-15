#!/usr/bin/env bash
# build.sh

set -o errexit  # exit on error

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "Build complete!"