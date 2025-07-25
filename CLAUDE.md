# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Start Development Server
```bash
uvicorn main:app --reload
```

### Database Management
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Downgrade migration
alembic downgrade -1
```

### Production Deployment
```bash
# Build for production (used by Render)
./build.sh

# Production start command
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Architecture Overview

This is a **FastAPI-based football/soccer management API** with the following core architecture:

### Single-File Monolith Structure
The entire application is contained in `main.py` (~892 lines), implementing a monolithic approach with:

- **FastAPI application** with CORS middleware
- **SQLAlchemy ORM** with declarative base models
- **Pydantic models** for request/response validation
- **Database session management** with dependency injection
- **Image upload handling** via Cloudinary with local fallback

### Database Models & Entities
1. **PlayerDB** - Core player management with skills, statistics, and photos
2. **PartitaDB** - Match/game records 
3. **FormazioneDB** - Team formations linking players to matches
4. **GolDB** - Goal records with assist tracking

### Key Features
- **Player Management**: CRUD operations with detailed skill ratings (1-10 scale)
- **Role-based Skills**: Different skill weightings for Goalkeeper, Defender, Midfielder, Forward
- **Match Management**: Complete match tracking with formations and goals
- **Image Uploads**: Cloudinary integration with local storage fallback
- **Statistics**: Player performance tracking and team analytics

### Skills System
Players have 9 skill attributes rated 1-10:
- **Basic Skills**: speed, passing, attack, defense, technique
- **Extended Skills**: goalkeeping, heading, stamina, leadership
- **Overall Rating**: Calculated based on player role with different weightings

### Environment Configuration
Required environment variables (see `.env` file):
- `DATABASE_URL` - PostgreSQL connection string
- `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` - Image upload service
- `ENVIRONMENT` - Deployment environment

### API Structure
RESTful endpoints under `/api/` prefix:
- `/api/players/*` - Player CRUD and photo upload
- `/api/partite/*` - Match management
- `/api/formazioni/*` - Team formation management  
- `/api/gol/*` - Goal tracking
- `/api/statistics` - Performance analytics

### Database Migration
Uses **Alembic** for database schema management. The `alembic/env.py` imports models from `main.py` and references `DATABASE_URL` environment variable.

### Deployment
Configured for **Render.com** deployment with:
- `build.sh` script for dependency installation
- `render.yaml` for service configuration  
- PostgreSQL database integration
- Static file serving for uploaded images