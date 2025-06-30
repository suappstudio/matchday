# Match Day Backend API

A FastAPI backend for managing football players, teams, and matches with image upload capabilities.

## Features

- Player management with detailed statistics
- Role-based player categorization (Goalkeeper, Defender, Midfielder, Forward)
- Image upload support via Cloudinary
- PostgreSQL database support
- Ready for deployment on Render

## Environment Variables

Create a `.env` file based on `env.example`:

```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@hostname:port/database_name

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Upload Configuration
MAX_UPLOAD_SIZE=5242880
ALLOWED_EXTENSIONS=.jpg,.jpeg,.png,.gif,.webp

# Environment
ENVIRONMENT=production
```

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env` file

3. Run the application:
```bash
uvicorn main:app --reload
```

## Deployment on Render

### Prerequisites

1. **Cloudinary Account**: Sign up at [cloudinary.com](https://cloudinary.com)
2. **GitHub Repository**: Your code should be in a GitHub repository

### Step 1: Set up Cloudinary

1. Get your Cloudinary credentials from your dashboard:
   - Cloud Name
   - API Key  
   - API Secret

### Step 2: Deploy to Render

1. Go to [render.com](https://render.com) and create an account
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository
4. Use these settings:
   - **Name**: `matchday-backend`
   - **Environment**: `Python`
   - **Build Command**: `./build.sh`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Step 3: Add Database

1. In Render dashboard, click "New +" and select "PostgreSQL"
2. Name it `matchday-db`
3. Choose the free plan
4. Once created, copy the connection string

### Step 4: Set Environment Variables

In your Render web service settings, add these environment variables:

- `DATABASE_URL`: Your PostgreSQL connection string from step 3
- `CLOUDINARY_CLOUD_NAME`: Your Cloudinary cloud name
- `CLOUDINARY_API_KEY`: Your Cloudinary API key
- `CLOUDINARY_API_SECRET`: Your Cloudinary API secret
- `ENVIRONMENT`: `production`

### Step 5: Deploy

Click "Deploy" and wait for the build to complete.

## API Endpoints

- `GET /` - API info
- `GET /health` - Health check
- `GET /api/players` - List all players
- `GET /api/players/{id}` - Get player details
- `POST /api/players` - Create new player
- `PUT /api/players/{id}` - Update player
- `DELETE /api/players/{id}` - Delete player
- `POST /api/players/{id}/photo` - Upload player photo
- `GET /api/statistics` - Get player statistics

## Database Schema

### Players Table
- `id`: Unique identifier
- `name`: Player name
- `role`: Player position (GOALKEEPER, DEFENDER, MIDFIELDER, FORWARD)
- `photo_url`: Cloudinary image URL
- `speed`, `strength`, `passing`, `attack`, `defense`, `technique`: Basic skills (1-10)
- `goalkeeping`, `heading`, `stamina`, `leadership`: Extended skills (1-10)
- `created_at`, `updated_at`: Timestamps