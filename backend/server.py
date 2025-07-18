from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class CompanySettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nom_societe: str
    numero_siret: str
    adresse: str
    telephone: str
    email: str
    # Tarifs configurables
    tarif_transfert_km: float = 2.0  # 2€/km par défaut
    tarif_mise_disposition_h: float = 80.0  # 80€/h par défaut
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CompanySettingsCreate(BaseModel):
    nom_societe: str
    numero_siret: str
    adresse: str
    telephone: str
    email: str
    tarif_transfert_km: float = 2.0
    tarif_mise_disposition_h: float = 80.0

class CompanySettingsUpdate(BaseModel):
    nom_societe: Optional[str] = None
    numero_siret: Optional[str] = None
    adresse: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    tarif_transfert_km: Optional[float] = None
    tarif_mise_disposition_h: Optional[float] = None

class Client(BaseModel):
    nom: str
    prenom: str
    adresse: str
    telephone: str
    email: str

class Devis(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    numero_devis: str
    date_creation: datetime = Field(default_factory=datetime.utcnow)
    date_validite: datetime
    client: Client
    type_prestation: str  # "transfert" or "mise_a_disposition"
    # Pour transfert
    adresse_prise_en_charge: Optional[str] = None
    adresse_destination: Optional[str] = None
    nombre_kilometres: Optional[float] = None
    # Pour mise à disposition
    nombre_heures: Optional[float] = None
    # Calculs
    prix_unitaire: float
    prix_ht: float
    taux_tva: float
    montant_tva: float
    prix_ttc: float
    is_facture: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DevisCreate(BaseModel):
    client: Client
    type_prestation: str
    adresse_prise_en_charge: Optional[str] = None
    adresse_destination: Optional[str] = None
    nombre_kilometres: Optional[float] = None
    nombre_heures: Optional[float] = None

# Routes pour les paramètres de société
@api_router.post("/company-settings", response_model=CompanySettings)
async def create_or_update_company_settings(settings: CompanySettingsCreate):
    # Vérifier s'il existe déjà des paramètres
    existing = await db.company_settings.find_one()
    
    if existing:
        # Mise à jour
        update_data = settings.dict()
        update_data["updated_at"] = datetime.utcnow()
        await db.company_settings.update_one(
            {"id": existing["id"]}, 
            {"$set": update_data}
        )
        updated_settings = await db.company_settings.find_one({"id": existing["id"]})
        return CompanySettings(**updated_settings)
    else:
        # Création
        settings_dict = settings.dict()
        settings_obj = CompanySettings(**settings_dict)
        await db.company_settings.insert_one(settings_obj.dict())
        return settings_obj

@api_router.get("/company-settings", response_model=CompanySettings)
async def get_company_settings():
    settings = await db.company_settings.find_one()
    if not settings:
        raise HTTPException(status_code=404, detail="Paramètres de société non trouvés")
    return CompanySettings(**settings)

# Routes pour les devis
@api_router.post("/devis", response_model=Devis)
async def create_devis(devis_data: DevisCreate):
    # Récupérer les paramètres de société pour les tarifs
    company_settings = await db.company_settings.find_one()
    if not company_settings:
        raise HTTPException(status_code=400, detail="Paramètres de société non configurés. Veuillez configurer vos tarifs d'abord.")
    
    # Génération du numéro de devis
    count = await db.devis.count_documents({})
    numero_devis = f"DEV-{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"
    
    # Calcul des prix selon le type de prestation avec tarifs configurés
    if devis_data.type_prestation == "transfert":
        if not devis_data.nombre_kilometres:
            raise HTTPException(status_code=400, detail="Nombre de kilomètres requis pour un transfert")
        prix_unitaire = company_settings.get("tarif_transfert_km", 2.0)  # Utiliser tarif configuré
        prix_ht = devis_data.nombre_kilometres * prix_unitaire
        taux_tva = 0.10  # 10% TVA
    elif devis_data.type_prestation == "mise_a_disposition":
        if not devis_data.nombre_heures:
            raise HTTPException(status_code=400, detail="Nombre d'heures requis pour une mise à disposition")
        prix_unitaire = company_settings.get("tarif_mise_disposition_h", 80.0)  # Utiliser tarif configuré
        prix_ht = devis_data.nombre_heures * prix_unitaire
        taux_tva = 0.20  # 20% TVA
    else:
        raise HTTPException(status_code=400, detail="Type de prestation invalide")
    
    montant_tva = prix_ht * taux_tva
    prix_ttc = prix_ht + montant_tva
    
    # Date de validité (30 jours)
    date_validite = datetime.now() + timedelta(days=30)
    
    # Création du devis
    devis_dict = devis_data.dict()
    devis_obj = Devis(
        numero_devis=numero_devis,
        date_validite=date_validite,
        prix_unitaire=prix_unitaire,
        prix_ht=prix_ht,
        taux_tva=taux_tva,
        montant_tva=montant_tva,
        prix_ttc=prix_ttc,
        **devis_dict
    )
    
    await db.devis.insert_one(devis_obj.dict())
    return devis_obj

@api_router.get("/devis", response_model=List[Devis])
async def get_all_devis():
    devis_list = await db.devis.find().sort("created_at", -1).to_list(1000)
    return [Devis(**devis) for devis in devis_list]

@api_router.get("/devis/{devis_id}", response_model=Devis)
async def get_devis(devis_id: str):
    devis = await db.devis.find_one({"id": devis_id})
    if not devis:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    return Devis(**devis)

@api_router.put("/devis/{devis_id}/convert-to-facture", response_model=Devis)
async def convert_to_facture(devis_id: str):
    devis = await db.devis.find_one({"id": devis_id})
    if not devis:
        raise HTTPException(status_code=404, detail="Devis non trouvé")
    
    # Mettre à jour pour indiquer qu'il s'agit d'une facture
    await db.devis.update_one(
        {"id": devis_id},
        {"$set": {"is_facture": True}}
    )
    
    updated_devis = await db.devis.find_one({"id": devis_id})
    return Devis(**updated_devis)

@api_router.get("/factures", response_model=List[Devis])
async def get_all_factures():
    factures_list = await db.devis.find({"is_facture": True}).sort("created_at", -1).to_list(1000)
    return [Devis(**facture) for facture in factures_list]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()