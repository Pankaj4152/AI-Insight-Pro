from fastapi import APIRouter, HTTPException, Query
from app.models import AddSDEModel
from app.database import get_connection_history, get_industry_classifications, get_sde_by_industry, add_sde

router = APIRouter(tags=["general"])


@router.get("/connection-history/{client_id}")
async def get_client_connection_history(client_id: str):
    """Get connection history for a specific client."""
    try:
        return get_connection_history(client_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/industry-classifications")
def get_industry_classifications_endpoint():
    """Get all available industry classifications."""
    try:
        return get_industry_classifications()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-sde")
def get_sde_endpoint(selected_industry: str = Query(...)):
    """Get SDEs for a specific industry."""
    try:
        return get_sde_by_industry(selected_industry)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-sde")
def add_sde_endpoint(sde: AddSDEModel):
    """Add a new SDE to the catalogue."""
    try:
        return add_sde(sde)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
