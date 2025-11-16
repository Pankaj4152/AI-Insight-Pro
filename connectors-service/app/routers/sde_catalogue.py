from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from agents.sde_agent import SDEAgent

router = APIRouter()
sde_agent = None

def get_sde_agent():
    global sde_agent
    if sde_agent is None:
        sde_agent = SDEAgent()
    return sde_agent

class SelectedSDE(BaseModel):
    pattern_name: str
    sensitivity: str
    protection_method: str

class SaveSelectedSDEsRequest(BaseModel):
    client_id: str
    selected_sdes: List[SelectedSDE]

@router.get("/client/{client_id}/industry")
def get_client_industry(client_id: str):
    """
    Get the registered industry for a client.
    """
    try:
        agent = get_sde_agent()
        industry = agent.get_client_industry(client_id)
        if industry is None:
            raise HTTPException(status_code=404, detail=f"Client {client_id} not found or no industry registered")
        return {
            "status": "success",
            "client_id": client_id,
            "industry": industry
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting client industry: {str(e)}")

@router.get("/industries/available")
def get_available_industries():
    """
    Get all available industries for filtering SDEs.
    """
    try:
        agent = get_sde_agent()
        industries = agent.get_available_industries()
        return {
            "status": "success",
            "count": len(industries),
            "industries": industries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting available industries: {str(e)}")

@router.get("/sdes/available")
def get_available_sdes(industry_filter: Optional[str] = None):
    """
    Get all available SDE patterns, optionally filtered by industry.
    """
    try:
        agent = get_sde_agent()
        sdes = agent.get_available_sdes(industry_filter)
        return {
            "status": "success",
            "count": len(sdes),
            "sdes": sdes,
            "industry_filter": industry_filter
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting available SDEs: {str(e)}")

@router.post("/sdes/save-selected")
def save_client_selected_sdes(request: SaveSelectedSDEsRequest):
    """
    Save the SDEs selected by a client.
    """
    try:
        agent = get_sde_agent()
        
        # Convert Pydantic models to dictionaries
        selected_sdes = [sde.dict() for sde in request.selected_sdes]
        
        success = agent.save_client_selected_sdes(request.client_id, selected_sdes)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save selected SDEs")
        
        return {
            "status": "success",
            "message": f"Successfully saved {len(selected_sdes)} selected SDEs for client {request.client_id}",
            "client_id": request.client_id,
            "saved_count": len(selected_sdes)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving selected SDEs: {str(e)}")

@router.get("/client/{client_id}/selected-sdes")
def get_client_selected_sdes(client_id: str):
    """
    Get the SDEs that a client has selected.
    """
    try:
        agent = get_sde_agent()
        selected_sdes = agent.get_client_selected_sdes(client_id)
        return {
            "status": "success",
            "client_id": client_id,
            "count": len(selected_sdes),
            "selected_sdes": selected_sdes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting client selected SDEs: {str(e)}")

@router.get("/catalogue/{client_id}")
def get_sde_catalogue(client_id: str, industry_filter: Optional[str] = None):
    """
    Get complete SDE catalogue information for a client including their industry and available SDEs.
    """
    try:
        agent = get_sde_agent()
        
        # Get client industry
        industry = agent.get_client_industry(client_id)
        if industry is None:
            raise HTTPException(status_code=404, detail=f"Client {client_id} not found or no industry registered")
        
        # Get available SDEs
        available_sdes = agent.get_available_sdes(industry_filter)
        
        # Get client's previously selected SDEs
        selected_sdes = agent.get_client_selected_sdes(client_id)
        
        return {
            "status": "success",
            "client_id": client_id,
            "registered_industry": industry,
            "available_sdes": {
                "count": len(available_sdes),
                "sdes": available_sdes
            },
            "selected_sdes": {
                "count": len(selected_sdes),
                "sdes": selected_sdes
            },
            "industry_filter": industry_filter
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting SDE catalogue: {str(e)}") 