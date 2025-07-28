#!/usr/bin/env python3
"""
Match Day Backend API
Gestisce giocatori, squadre e partite con upload immagini
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date, time
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

class SquadraEnum(str, enum.Enum):
    A = "A"
    B = "B"

class TipoGolEnum(str, enum.Enum):
    NORMALE = "normale"
    RIGORE = "rigore"
    AUTORETE = "autorete"
    PUNIZIONE = "punizione"

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

    # Statistics
    goals_scored = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    gold_medals = Column(Integer, default=0)
    silver_medals = Column(Integer, default=0)
    bronze_medals = Column(Integer, default=0)

class PartitaDB(Base):
    __tablename__ = "partite"
    id = Column(Integer, primary_key=True, autoincrement=True)
    data_partita = Column(DateTime, nullable=False)
    ora_inizio = Column(String) # TIME in SQL is often represented as string or timedelta in Python
    nome_squadra_a = Column(String(100))
    nome_squadra_b = Column(String(100))
    gol_squadra_a = Column(Integer, default=0)
    gol_squadra_b = Column(Integer, default=0)
    stadio = Column(String(100))
    arbitro = Column(String(100))
    note = Column(String)
    numero_giocatori_squadra = Column(Integer, default=11)

class FormazioneDB(Base):
    __tablename__ = "formazioni"
    id = Column(Integer, primary_key=True, autoincrement=True)
    partita_id = Column(Integer, ForeignKey('partite.id'), nullable=False)
    giocatore_id = Column(String, ForeignKey('players.id'), nullable=False)
    squadra = Column(SQLEnum(SquadraEnum), nullable=False)
    numero_maglia = Column(Integer)
    capitano = Column(Boolean, default=False)
    __table_args__ = (UniqueConstraint('partita_id', 'giocatore_id', name='unique_player_match'),)

class GolDB(Base):
    __tablename__ = "gol"
    id = Column(Integer, primary_key=True, autoincrement=True)
    partita_id = Column(Integer, ForeignKey('partite.id'), nullable=False)
    giocatore_id = Column(String, ForeignKey('players.id'), nullable=False)
    minuto = Column(Integer, nullable=False)
    squadra = Column(SQLEnum(SquadraEnum), nullable=False)
    tipo_gol = Column(SQLEnum(TipoGolEnum), default='normale')
    assist_giocatore_id = Column(String, ForeignKey('players.id'), nullable=True)

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
    goals_scored: int = 0
    assists: int = 0
    gold_medals: int = 0
    silver_medals: int = 0
    bronze_medals: int = 0

class PlayerCreate(PlayerBase):
    pass

class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[PlayerRole] = None
    skills: Optional[PlayerSkills] = None
    goals_scored: Optional[int] = None
    assists: Optional[int] = None
    gold_medals: Optional[int] = None
    silver_medals: Optional[int] = None
    bronze_medals: Optional[int] = None

class Player(PlayerBase):
    id: str
    photo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    goals_scored: int
    assists: int
    gold_medals: int
    silver_medals: int
    bronze_medals: int
    
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
    goals_scored: int
    assists: int
    gold_medals: int
    silver_medals: int
    bronze_medals: int
    
    class Config:
        from_attributes = True

# Pydantic Models for Partite
class PartitaBase(BaseModel):
    data_partita: date
    ora_inizio: Optional[time] = None
    nome_squadra_a: Optional[str] = None
    nome_squadra_b: Optional[str] = None
    gol_squadra_a: int = 0
    gol_squadra_b: int = 0
    stadio: Optional[str] = None
    arbitro: Optional[str] = None
    note: Optional[str] = None
    numero_giocatori_squadra: Optional[int] = None

class PartitaCreate(PartitaBase):
    pass

class PartitaUpdate(BaseModel):
    data_partita: Optional[date] = None
    ora_inizio: Optional[time] = None
    nome_squadra_a: Optional[str] = None
    nome_squadra_b: Optional[str] = None
    gol_squadra_a: Optional[int] = None
    gol_squadra_b: Optional[int] = None
    stadio: Optional[str] = None
    arbitro: Optional[str] = None
    note: Optional[str] = None
    numero_giocatori_squadra: Optional[int] = None

class Partita(PartitaBase):
    id: int

    class Config:
        from_attributes = True

# Pydantic Models for Formazioni
class FormazioneBase(BaseModel):
    partita_id: int
    giocatore_id: str
    squadra: SquadraEnum
    numero_maglia: Optional[int] = None
    capitano: bool = False

class FormazioneCreate(FormazioneBase):
    pass

class FormazioneUpdate(BaseModel):
    partita_id: Optional[int] = None
    giocatore_id: Optional[str] = None
    squadra: Optional[SquadraEnum] = None
    numero_maglia: Optional[int] = None
    capitano: Optional[bool] = None

class Formazione(FormazioneBase):
    id: int

    class Config:
        from_attributes = True

class FormazioneDetail(Formazione):
    giocatore: Player

    class Config:
        from_attributes = True

# Pydantic Models for Gol
class GolBase(BaseModel):
    partita_id: int
    giocatore_id: str
    minuto: int
    squadra: SquadraEnum
    tipo_gol: TipoGolEnum = TipoGolEnum.NORMALE
    assist_giocatore_id: Optional[str] = None

class GolCreate(GolBase):
    pass

class Gol(GolBase):
    id: int

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
    except Exception:
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
            "updated_at": player.updated_at,
            "goals_scored": player.goals_scored,
            "assists": player.assists,
            "gold_medals": player.gold_medals,
            "silver_medals": player.silver_medals,
            "bronze_medals": player.bronze_medals
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
        overall_rating=calculate_overall_rating(player),
        goals_scored=player.goals_scored,
        assists=player.assists,
        gold_medals=player.gold_medals,
        silver_medals=player.silver_medals,
        bronze_medals=player.bronze_medals
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
        leadership=player.skills.leadership,
        goals_scored=player.goals_scored,
        assists=player.assists,
        gold_medals=player.gold_medals,
        silver_medals=player.silver_medals,
        bronze_medals=player.bronze_medals
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
        updated_at=db_player.updated_at,
        goals_scored=db_player.goals_scored,
        assists=db_player.assists,
        gold_medals=db_player.gold_medals,
        silver_medals=db_player.silver_medals,
        bronze_medals=db_player.bronze_medals
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
    
    if player_update.goals_scored is not None:
        player.goals_scored = player_update.goals_scored
    if player_update.assists is not None:
        player.assists = player_update.assists
    if player_update.gold_medals is not None:
        player.gold_medals = player_update.gold_medals
    if player_update.silver_medals is not None:
        player.silver_medals = player_update.silver_medals
    if player_update.bronze_medals is not None:
        player.bronze_medals = player_update.bronze_medals
    
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

# ----- PARTITE ENDPOINTS -----

@app.post("/api/partite", response_model=Partita)
def create_partita(partita: PartitaCreate, db: Session = Depends(get_db)):
    """Crea una nuova partita"""
    db_partita = PartitaDB(
        data_partita=partita.data_partita,
        ora_inizio=partita.ora_inizio.strftime("%H:%M:%S") if partita.ora_inizio else None,
        nome_squadra_a=partita.nome_squadra_a,
        nome_squadra_b=partita.nome_squadra_b,
        gol_squadra_a=partita.gol_squadra_a,
        gol_squadra_b=partita.gol_squadra_b,
        stadio=partita.stadio,
        arbitro=partita.arbitro,
        note=partita.note,
        numero_giocatori_squadra=partita.numero_giocatori_squadra
    )
    db.add(db_partita)
    db.commit()
    db.refresh(db_partita)
    return db_partita

@app.get("/api/partite", response_model=List[Partita])
def get_partite(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Ottieni la lista di tutte le partite"""
    partite = db.query(PartitaDB).offset(skip).limit(limit).all()
    return partite

@app.get("/api/partite/{partita_id}", response_model=Partita)
def get_partita(partita_id: int, db: Session = Depends(get_db)):
    """Ottieni i dettagli di una singola partita"""
    partita = db.query(PartitaDB).filter(PartitaDB.id == partita_id).first()
    if not partita:
        raise HTTPException(status_code=404, detail="Partita not found")
    return partita

@app.put("/api/partite/{partita_id}", response_model=Partita)
def update_partita(partita_id: int, partita_update: PartitaUpdate, db: Session = Depends(get_db)):
    """Aggiorna i dati di una partita"""
    partita = db.query(PartitaDB).filter(PartitaDB.id == partita_id).first()
    if not partita:
        raise HTTPException(status_code=404, detail="Partita not found")

    update_data = partita_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "ora_inizio" and value is not None:
            setattr(partita, key, value.strftime("%H:%M:%S"))
        else:
            setattr(partita, key, value)
    
    db.commit()
    db.refresh(partita)
    return partita

@app.delete("/api/partite/{partita_id}")
def delete_partita(partita_id: int, db: Session = Depends(get_db)):
    """Elimina una partita"""
    partita = db.query(PartitaDB).filter(PartitaDB.id == partita_id).first()
    if not partita:
        raise HTTPException(status_code=404, detail="Partita not found")
    db.delete(partita)
    db.commit()
    return {"message": "Partita deleted successfully"}

# ----- FORMAZIONI ENDPOINTS -----

@app.post("/api/formazioni", response_model=List[Formazione])
def create_formazione(formazioni: List[FormazioneCreate], db: Session = Depends(get_db)):
    """Aggiunge uno o più giocatori ad una formazione di una partita"""
    created_formazioni = []
    for formazione in formazioni:
        # Check if partita_id exists
        partita = db.query(PartitaDB).filter(PartitaDB.id == formazione.partita_id).first()
        if not partita:
            raise HTTPException(status_code=404, detail=f"Partita with ID {formazione.partita_id} not found")
        
        # Check if giocatore_id exists
        giocatore = db.query(PlayerDB).filter(PlayerDB.id == formazione.giocatore_id).first()
        if not giocatore:
            raise HTTPException(status_code=404, detail=f"Giocatore with ID {formazione.giocatore_id} not found")

        db_formazione = FormazioneDB(
            partita_id=formazione.partita_id,
            giocatore_id=formazione.giocatore_id,
            squadra=formazione.squadra,
            numero_maglia=formazione.numero_maglia,
            capitano=formazione.capitano
        )
        try:
            db.add(db_formazione)
            db.commit()
            db.refresh(db_formazione)
            created_formazioni.append(Formazione.model_validate(db_formazione))
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Error creating formazione for player {formazione.giocatore_id}: {e}")
    return created_formazioni

@app.get("/api/formazioni", response_model=List[Formazione])
def get_formazioni(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Ottieni la lista di tutte le formazioni"""
    formazioni = db.query(FormazioneDB).offset(skip).limit(limit).all()
    return formazioni

@app.get("/api/formazioni/{formazione_id}", response_model=Formazione)
def get_formazione(formazione_id: int, db: Session = Depends(get_db)):
    """Ottieni i dettagli di una singola formazione"""
    formazione = db.query(FormazioneDB).filter(FormazioneDB.id == formazione_id).first()
    if not formazione:
        raise HTTPException(status_code=404, detail="Formazione not found")
    return formazione

@app.delete("/api/formazioni/{formazione_id}")
def delete_formazione(formazione_id: int, db: Session = Depends(get_db)):
    """Elimina una formazione"""
    formazione = db.query(FormazioneDB).filter(FormazioneDB.id == formazione_id).first()
    if not formazione:
        raise HTTPException(status_code=404, detail="Formazione not found")
    db.delete(formazione)
    db.commit()
    return {"message": "Formazione deleted successfully"}

@app.get("/api/partite/{partita_id}/formazioni", response_model=List[FormazioneDetail])
def get_formazioni_by_partita(partita_id: int, db: Session = Depends(get_db)):
    """Ottieni le formazioni per una specifica partita, inclusi i dettagli dei giocatori"""
    formazioni_db = db.query(FormazioneDB).filter(FormazioneDB.partita_id == partita_id).all()
    if not formazioni_db:
        raise HTTPException(status_code=404, detail="Formazioni not found for this partita")
    
    formazioni_detail = []
    for f_db in formazioni_db:
        player_db = db.query(PlayerDB).filter(PlayerDB.id == f_db.giocatore_id).first()
        if not player_db:
            # This should ideally not happen if FK constraints are enforced
            raise HTTPException(status_code=500, detail=f"Player with ID {f_db.giocatore_id} not found for formazione {f_db.id}")
        
        player_skills = PlayerSkills(
            speed=player_db.speed,
            passing=player_db.passing,
            attack=player_db.attack,
            defense=player_db.defense,
            technique=player_db.technique,
            goalkeeping=player_db.goalkeeping,
            heading=player_db.heading,
            stamina=player_db.stamina,
            leadership=player_db.leadership
        )

        player_model = Player(
            id=player_db.id,
            name=player_db.name,
            role=player_db.role,
            photo_url=player_db.photo_url,
            skills=player_skills,
            created_at=player_db.created_at,
            updated_at=player_db.updated_at,
            goals_scored=player_db.goals_scored,
            assists=player_db.assists,
            gold_medals=player_db.gold_medals,
            silver_medals=player_db.silver_medals,
            bronze_medals=player_db.bronze_medals
        )

        formazioni_detail.append(FormazioneDetail(
            id=f_db.id,
            partita_id=f_db.partita_id,
            giocatore_id=f_db.giocatore_id,
            squadra=f_db.squadra,
            numero_maglia=f_db.numero_maglia,
            capitano=f_db.capitano,
            giocatore=player_model
        ))
    return formazioni_detail

@app.put("/api/partite/{partita_id}/formazioni", response_model=List[Formazione])
def update_formazioni_by_partita(
    partita_id: int,
    formazioni: List[FormazioneCreate],
    db: Session = Depends(get_db)
):
    """Aggiorna tutte le formazioni di una partita (sostituisce completamente la formazione esistente)"""
    # Check if partita_id exists
    partita = db.query(PartitaDB).filter(PartitaDB.id == partita_id).first()
    if not partita:
        raise HTTPException(status_code=404, detail="Partita not found")
    
    # Delete existing formazioni for this partita
    db.query(FormazioneDB).filter(FormazioneDB.partita_id == partita_id).delete()
    
    # Create new formazioni
    created_formazioni = []
    for formazione in formazioni:
        # Validate that partita_id matches the URL parameter
        if formazione.partita_id != partita_id:
            raise HTTPException(status_code=400, detail=f"partita_id in body ({formazione.partita_id}) must match URL parameter ({partita_id})")
        
        # Check if giocatore_id exists
        giocatore = db.query(PlayerDB).filter(PlayerDB.id == formazione.giocatore_id).first()
        if not giocatore:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Giocatore with ID {formazione.giocatore_id} not found")

        db_formazione = FormazioneDB(
            partita_id=formazione.partita_id,
            giocatore_id=formazione.giocatore_id,
            squadra=formazione.squadra,
            numero_maglia=formazione.numero_maglia,
            capitano=formazione.capitano
        )
        
        try:
            db.add(db_formazione)
            db.flush()  # Flush to get the ID but don't commit yet
            created_formazioni.append(Formazione.model_validate(db_formazione))
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Error creating formazione for player {formazione.giocatore_id}: {e}")
    
    try:
        db.commit()
        return created_formazioni
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error committing formazioni changes: {e}")

# ----- GOL ENDPOINTS -----

@app.post("/api/gol", response_model=Gol)
def create_gol(gol: GolCreate, db: Session = Depends(get_db)):
    """Registra un gol"""
    # Check if partita_id exists
    partita = db.query(PartitaDB).filter(PartitaDB.id == gol.partita_id).first()
    if not partita:
        raise HTTPException(status_code=404, detail="Partita not found")
    
    # Check if giocatore_id exists
    giocatore = db.query(PlayerDB).filter(PlayerDB.id == gol.giocatore_id).first()
    if not giocatore:
        raise HTTPException(status_code=404, detail="Giocatore not found")

    # Check if assist_giocatore_id exists if provided
    if gol.assist_giocatore_id:
        assist_giocatore = db.query(PlayerDB).filter(PlayerDB.id == gol.assist_giocatore_id).first()
        if not assist_giocatore:
            raise HTTPException(status_code=404, detail="Assist player not found")

    db_gol = GolDB(
        partita_id=gol.partita_id,
        giocatore_id=gol.giocatore_id,
        minuto=gol.minuto,
        squadra=gol.squadra,
        tipo_gol=gol.tipo_gol,
        assist_giocatore_id=gol.assist_giocatore_id
    )
    db.add(db_gol)
    db.commit()
    db.refresh(db_gol)
    return db_gol

@app.get("/api/gol", response_model=List[Gol])
def get_gol(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Ottieni la lista di tutti i gol registrati"""
    gol = db.query(GolDB).offset(skip).limit(limit).all()
    return gol

@app.get("/api/gol/{gol_id}", response_model=Gol)
def get_gol_by_id(gol_id: int, db: Session = Depends(get_db)):
    """Ottieni i dettagli di un singolo gol"""
    gol = db.query(GolDB).filter(GolDB.id == gol_id).first()
    if not gol:
        raise HTTPException(status_code=404, detail="Gol not found")
    return gol

@app.delete("/api/gol/{gol_id}")
def delete_gol(gol_id: int, db: Session = Depends(get_db)):
    """Elimina un gol registrato"""
    gol = db.query(GolDB).filter(GolDB.id == gol_id).first()
    if not gol:
        raise HTTPException(status_code=404, detail="Gol not found")
    db.delete(gol)
    db.commit()
    return {"message": "Gol deleted successfully"}

@app.get("/api/partite/{partita_id}/gol", response_model=List[Gol])
def get_gol_by_partita(partita_id: int, db: Session = Depends(get_db)):
    """Ottieni tutti i gol di una specifica partita"""
    # Check if partita_id exists
    partita = db.query(PartitaDB).filter(PartitaDB.id == partita_id).first()
    if not partita:
        raise HTTPException(status_code=404, detail="Partita not found")
    
    gol = db.query(GolDB).filter(GolDB.partita_id == partita_id).all()
    return gol

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
