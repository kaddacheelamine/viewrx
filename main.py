from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from urllib.parse import quote

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_KEY in .env file")

supabase: Client = create_client(supabase_url, supabase_key)

app = FastAPI()

# Configure CORS
origins = [
    "*",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Medicine(BaseModel):
    name: str
    dosage: str
    frequency: str
    note: str

class FormData(BaseModel):
    drid: int
    sendToValue: str
    patientName: str
    patientAge: str
    patientDescription: str
    currentDate: str
    medicines: List[Medicine]

class PrescriptionResponse(BaseModel):
    id: int
    drid: int
    sendToValue: str
    patientName: str
    patientAge: str
    patientDescription: str
    currentDate: str
    medicines: List[Medicine]

@app.post("/prescriptions/", response_model=PrescriptionResponse)
async def create_prescription(form_data: FormData):
    """
    Store a new prescription in the database.
    """
    try:
        # Convert Medicine objects to dictionaries for storage
        prescription_data = form_data.dict()
        prescription_data["medicines"] = [med.dict() for med in form_data.medicines]
        
        # Insert into Supabase
        result = supabase.table("prescriptions").insert(prescription_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to store prescription")
        
        # Get the ID of the newly created prescription
        new_prescription = result.data[0]
        
        # Re-convert medicine dictionaries to objects
        new_prescription["medicines"] = [Medicine(**med) for med in new_prescription["medicines"]]
        
        return PrescriptionResponse(**new_prescription)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/prescriptions/", response_model=List[PrescriptionResponse])
async def get_prescriptions(drid: Optional[int] = None):
    """
    Get all prescriptions or filter by doctor ID.
    """
    try:
        query = supabase.table("prescriptions")
        
        # If drid is provided, filter by doctor ID
        if drid:
            query = query.eq("drid", drid)
        
        result = query.execute()
        
        if not result.data:
            return []
        
        # Convert medicine dictionaries back to Medicine objects
        prescriptions = []
        for prescription in result.data:
            prescription["medicines"] = [Medicine(**med) for med in prescription["medicines"]]
            prescriptions.append(PrescriptionResponse(**prescription))
        
        return prescriptions
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/prescriptions/{prescription_id}", response_model=PrescriptionResponse)
async def get_prescription(prescription_id: int):
    """
    Get a specific prescription by ID.
    """
    try:
        result = supabase.table("prescriptions").select("*").eq("id", prescription_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        prescription = result.data[0]
        prescription["medicines"] = [Medicine(**med) for med in prescription["medicines"]]
        
        return PrescriptionResponse(**prescription)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.delete("/prescriptions/{prescription_id}")
async def delete_prescription(prescription_id: int):
    """
    Delete a prescription by ID.
    """
    try:
        result = supabase.table("prescriptions").delete().eq("id", prescription_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Prescription not found")
        
        return {"message": "Prescription deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Run the application8000)
