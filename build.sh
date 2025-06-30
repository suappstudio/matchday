#!/usr/bin/env bash
# build.sh

set -o errexit  # exit on error

pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
python -c "
from main import Base, engine
print('Creating database tables...')
Base.metadata.create_all(bind=engine)
print('Database setup complete!')
"