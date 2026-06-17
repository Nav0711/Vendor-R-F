from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, engine
from models import VendorInput, Base
import json

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="VendorLens Prototype")

# Enable CORS for frontend testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ PYDANTIC MODELS ============

class DirectorInput(BaseModel):
    name: str
    position: str = None

class UBOInput(BaseModel):
    name: str
    ownership_pct: float = None

class VendorIntakeRequest(BaseModel):
    legal_name: str
    jurisdiction: str = "US"
    registration_number: str = None
    directors: list[DirectorInput] = []
    ubo: list[UBOInput] = []
    website_url: str = None

class VendorIntakeResponse(BaseModel):
    input_id: str
    legal_name: str
    message: str

# ============ ENDPOINTS ============

@app.post("/api/v1/vendor/intake", response_model=VendorIntakeResponse)
async def intake_vendor(request: VendorIntakeRequest, db: Session = Depends(get_db)):
    """Accept vendor data and store in DB."""
    try:
        vendor = VendorInput(
            legal_name=request.legal_name,
            jurisdiction=request.jurisdiction,
            registration_number=request.registration_number,
            directors=[d.dict() for d in request.directors],
            ubo=[u.dict() for u in request.ubo],
            website_url=request.website_url
        )
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        
        return VendorIntakeResponse(
            input_id=vendor.input_id,
            legal_name=vendor.legal_name,
            message="Vendor intake recorded. Call /scan to start screening."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check for load balancer."""
    return {"status": "healthy"}
