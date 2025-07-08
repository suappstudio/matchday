#!/usr/bin/env python3
"""
Match Day Backend API
Gestisce giocatori, squadre e partite con upload immagini
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import uuid4
import os
import shutil
from pathlib import Path
import enum
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ===== CONFIGURAZIONE =====
app = FastAPI(title="Match Day API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specifica gli origin permessi
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Handle Render's postgres URL format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


# Directories setup (kept for backward compatibility)
UPLOAD_DIR = Path("uploads/players")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Serve static files (kept for backward compatibility)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ===== ENUMS =====
class PlayerRole(str, enum.Enum):
    GOALKEEPER = "GOALKEEPER"
    DEFENDER = "DEFENDER"
    MIDFIELDER = "MIDFIELDER"
    FORWARD = "FORWARD"

# ===== DATABASE MODELS =====
class PlayerDB(Base):
    __tablename__ = "players"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    role = Column(SQLEnum(PlayerRole), nullable=False)
    photo_url = Column(String, nullable=True)
    
    # Skills
    speed = Column(Integer, default=5)
    passing = Column(Integer, default=5)
    attack = Column(Integer, default=5)
    defense = Column(Integer, default=5)
    technique = Column(Integer, default=5)
    
    # Extended skills for PlayerDetail
    goalkeeping = Column(Integer, default=5)
    heading = Column(Integer, default=5)
    stamina = Column(Integer, default=5)
    leadership = Column(Integer, default=5)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# ===== PYDANTIC MODELS =====
class PlayerSkills(BaseModel):
    speed: int = Field(ge=1, le=10, default=5)
    passing: int = Field(ge=1, le=10, default=5)
    attack: int = Field(ge=1, le=10, default=5)
    defense: int = Field(ge=1, le=10, default=5)
    technique: int = Field(ge=1, le=10, default=5)
    goalkeeping: int = Field(ge=1, le=10, default=5)
    heading: int = Field(ge=1, le=10, default=5)
    stamina: int = Field(ge=1, le=10, default=5)
    leadership: int = Field(ge=1, le=10, default=5)



class PlayerBase(BaseModel):
    name: str
    role: PlayerRole
    skills: PlayerSkills

class PlayerCreate(PlayerBase):
    pass

class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[PlayerRole] = None
    skills: Optional[PlayerSkills] = None

class Player(PlayerBase):
    id: str
    photo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PlayerDetail(BaseModel):
    id: str
    name: str
    role: PlayerRole
    photo_url: Optional[str] = None
    skills: PlayerSkills
    created_at: datetime
    updated_at: datetime
    overall_rating: int
    
    class Config:
        from_attributes = True

# ===== DEPENDENCIES =====
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===== UTILITY FUNCTIONS =====
def calculate_overall_rating(player: PlayerDB) -> int:
    """Calcola il rating complessivo basato sul ruolo"""
    if player.role == PlayerRole.GOALKEEPER:
        return int((player.goalkeeping * 3 + player.defense * 2 + player.technique + player.leadership) / 7)
    elif player.role == PlayerRole.DEFENDER:
        return int((player.defense * 3 + player.heading * 2 + player.passing + player.stamina + player.leadership) / 8)
    elif player.role == PlayerRole.MIDFIELDER:
        return int((player.passing * 2 + player.technique * 2 + player.stamina + player.attack + player.defense + player.leadership) / 8)
    else:  # FORWARD
        return int((player.attack * 3 + player.speed * 2 + player.technique + player.heading + player.stamina) / 8)

def save_upload_file(upload_file: UploadFile, player_id: str) -> str:
    """Upload file to Cloudinary and return the URL"""
    try:
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            upload_file.file,
            public_id=f"players/{player_id}",
            folder="matchday",
            resource_type="image",
            transformation=[
                {"width": 400, "height": 400, "crop": "fill", "gravity": "face"},
                {"quality": "auto", "fetch_format": "auto"}
            ]
        )
        return result["secure_url"]
    except Exception as e:
        # Fallback to local storage if Cloudinary fails
        file_extension = Path(upload_file.filename).suffix
        file_name = f"{player_id}{file_extension}"
        file_path = UPLOAD_DIR / file_name
        
        upload_file.file.seek(0)  # Reset file pointer
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        
        return f"/uploads/players/{file_name}"

# ===== API ENDPOINTS =====

@app.get("/")
def root():
    return {"message": "Match Day API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database": "connected"
    }

# ----- PLAYERS ENDPOINTS -----

@app.get("/api/players", response_model=List[Player])
def get_players(
    skip: int = 0,
    limit: int = 100,
    role: Optional[PlayerRole] = None,
    db: Session = Depends(get_db)
):
    """Ottieni la lista di tutti i giocatori"""
    query = db.query(PlayerDB)
    
    if role:
        query = query.filter(PlayerDB.role == role)
    
    players = query.offset(skip).limit(limit).all()
    
    # Converti in formato response
    result = []
    for player in players:
        player_dict = {
            "id": player.id,
            "name": player.name,
            "role": player.role,
            "photo_url": player.photo_url,
            "skills": {
                "speed": player.speed,
                "passing": player.passing,
                "attack": player.attack,
                "defense": player.defense,
                "technique": player.technique,
                "goalkeeping":player.goalkeeping,
                "heading":player.heading,
                "stamina":player.stamina,
                "leadership":player.leadership
            },
            "created_at": player.created_at,
            "updated_at": player.updated_at
        }
        result.append(Player(**player_dict))
    
    return result

@app.get("/api/players/{player_id}", response_model=PlayerDetail)
def get_player(player_id: str, db: Session = Depends(get_db)):
    """Ottieni i dettagli di un singolo giocatore"""
    player = db.query(PlayerDB).filter(PlayerDB.id == player_id).first()
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    return PlayerDetail(
        id=player.id,
        name=player.name,
        role=player.role,
        photo_url=player.photo_url,
        skills=PlayerSkills(
            speed=player.speed,
            passing=player.passing,
            attack=player.attack,
            defense=player.defense,
            technique=player.technique,
            goalkeeping=player.goalkeeping,
            heading=player.heading,
            stamina=player.stamina,
            leadership=player.leadership
        ),
        created_at=player.created_at,
        updated_at=player.updated_at,
        overall_rating=calculate_overall_rating(player)
    )

@app.post("/api/players", response_model=Player)
def create_player(player: PlayerCreate, db: Session = Depends(get_db)):
    """Crea un nuovo giocatore"""
    db_player = PlayerDB(
        name=player.name,
        role=player.role,
        speed=player.skills.speed,
        passing=player.skills.passing,
        attack=player.skills.attack,
        defense=player.skills.defense,
        technique=player.skills.technique,
        goalkeeping=player.skills.goalkeeping,
        heading=player.skills.heading,
        stamina=player.skills.stamina,
        leadership=player.skills.leadership
    )
    
    # Set default extended skills based on role
    if player.role == PlayerRole.GOALKEEPER:
        db_player.goalkeeping = 8
    
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    
    return Player(
        id=db_player.id,
        name=db_player.name,
        role=db_player.role,
        photo_url=db_player.photo_url,
        skills=PlayerSkills(
            speed=db_player.speed,
            passing=db_player.passing,
            attack=db_player.attack,
            defense=db_player.defense,
            technique=db_player.technique,
            goalkeeping=db_player.goalkeeping,
            heading=db_player.heading,
            stamina=db_player.stamina,
            leadership=db_player.leadership
            
        ),
        created_at=db_player.created_at,
        updated_at=db_player.updated_at
    )

@app.put("/api/players/{player_id}", response_model=PlayerDetail)
def update_player(
    player_id: str,
    player_update: PlayerUpdate,
    db: Session = Depends(get_db)
):
    """Aggiorna i dati di un giocatore"""
    player = db.query(PlayerDB).filter(PlayerDB.id == player_id).first()
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if player_update.name is not None:
        player.name = player_update.name
    
    if player_update.role is not None:
        player.role = player_update.role
    
    if player_update.skills is not None:
        player.speed = player_update.skills.speed
        player.passing = player_update.skills.passing
        player.attack = player_update.skills.attack
        player.defense = player_update.skills.defense
        player.technique = player_update.skills.technique
        player.goalkeeping = player_update.skills.goalkeeping
        player.heading = player_update.skills.heading
        player.stamina = player_update.skills.stamina
        player.leadership = player_update.skills.leadership
    
    player.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(player)
    
    return get_player(player_id, db)

@app.delete("/api/players/{player_id}")
def delete_player(player_id: str, db: Session = Depends(get_db)):
    """Elimina un giocatore"""
    player = db.query(PlayerDB).filter(PlayerDB.id == player_id).first()
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Delete photo if exists
    if player.photo_url:
        # If it's a Cloudinary URL, delete from Cloudinary
        if "cloudinary.com" in player.photo_url:
            try:
                # Extract public_id from URL
                public_id = player.photo_url.split("/")[-1].split(".")[0]
                cloudinary.uploader.destroy(f"matchday/players/{public_id}")
            except Exception:
                pass  # Continue even if deletion fails
        else:
            # Local file deletion
            file_path = Path(".") / player.photo_url.lstrip("/")
            if file_path.exists():
                file_path.unlink()
    
    db.delete(player)
    db.commit()
    
    return {"message": "Player deleted successfully"}

# ----- PHOTO UPLOAD ENDPOINT -----

@app.post("/api/players/{player_id}/photo")
async def upload_player_photo(
    player_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Carica o aggiorna la foto profilo di un giocatore"""
    player = db.query(PlayerDB).filter(PlayerDB.id == player_id).first()
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Validate file type
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed types: {allowed_extensions}")
    
    # Delete old photo if exists
    if player.photo_url:
        # If it's a Cloudinary URL, delete from Cloudinary
        if "cloudinary.com" in player.photo_url:
            try:
                # Extract public_id from URL
                public_id = player.photo_url.split("/")[-1].split(".")[0]
                cloudinary.uploader.destroy(f"matchday/players/{public_id}")
            except Exception:
                pass  # Continue even if deletion fails
        else:
            # Local file deletion
            old_file_path = Path(".") / player.photo_url.lstrip("/")
            if old_file_path.exists():
                old_file_path.unlink()
    
    # Save new photo
    photo_url = save_upload_file(file, player_id)
    player.photo_url = photo_url
    player.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"photo_url": photo_url, "message": "Photo uploaded successfully"}

# ----- STATISTICS ENDPOINT -----

@app.get("/api/statistics")
def get_statistics(db: Session = Depends(get_db)):
    """Ottieni statistiche generali"""
    total_players = db.query(PlayerDB).count()
    
    players_by_role = {}
    for role in PlayerRole:
        count = db.query(PlayerDB).filter(PlayerDB.role == role).count()
        players_by_role[role.value] = count
    
    # Average skills
    all_players = db.query(PlayerDB).all()
    if all_players:
        avg_skills = {
            "speed": sum(p.speed for p in all_players) / len(all_players),
            "passing": sum(p.passing for p in all_players) / len(all_players),
            "attack": sum(p.attack for p in all_players) / len(all_players),
            "defense": sum(p.defense for p in all_players) / len(all_players),
            "technique": sum(p.technique for p in all_players) / len(all_players),
            "goalkeeping": sum(p.goalkeeping for p in all_players) / len(all_players),
            "heading":sum(p.heading for p in all_players) / len(all_players),
            "stamina":sum(p.stamina for p in all_players) / len(all_players),
            "leadership":sum(p.leadership for p in all_players) / len(all_players),
        }
    else:
        avg_skills = {}
    
    return {
        "total_players": total_players,
        "players_by_role": players_by_role,
        "average_skills": avg_skills
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
