#!/usr/bin/env bash
# build.sh

set -o errexit  # exit on error

source .venv/bin/activate

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Run database migrations
python3 -c "
from main import Base, engine
print('Creating database tables...')
Base.metadata.create_all(bind=engine)
print('Database setup complete!')
"