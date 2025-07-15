#!/usr/bin/env bash
# build.sh

set -o errexit  # exit on error

source .venv/bin/activate

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Run database migrations
python3 -m alembic upgrade head

echo "Database setup complete!"