from fastapi import APIRouter, HTTPException, Body, Query
from uuid import UUID
from app.models import ModelInventoryModel
from app.database import DB_URL
import psycopg2

router = APIRouter(prefix="/model-inventory", tags=["model-inventory"])

# Valid industry use cases (matching frontend options)
VALID_INDUSTRIES = {
    "Healthcare", "Finance", "Retail", "Technology", "Manufacturing",
    "Education", "Government", "Media", "Automotive", "Energy", "Other"
}


@router.post("/add")
def add_model(model: ModelInventoryModel):
    # Validate industry use case if provided
    if model.industry_use_case and model.industry_use_case not in VALID_INDUSTRIES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid industry use case. Must be one of: {', '.join(VALID_INDUSTRIES)}"
        )
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO model_inventory (
                client_id, model_name, provider_name, weights_location, 
                bias_notes, description, industry_use_case, 
                data_store_types, compliance_requirements
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING model_id, created_at
        """, (
            model.client_id, model.model_name, model.provider_name, 
            model.weights_location, model.bias_notes, model.description,
            model.industry_use_case, model.data_store_types, 
            model.compliance_requirements
        ))
        row = cur.fetchone()
        conn.commit()
        return {"status": "success", "model_id": row[0], "created_at": row[1]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@router.get("/list")
def list_models(client_id: str = Query(...)):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                model_id, client_id, model_name, provider_name, weights_location, 
                bias_notes, description, industry_use_case, 
                data_store_types, compliance_requirements, created_at
            FROM model_inventory 
            WHERE client_id = %s
            ORDER BY created_at DESC
        """, (client_id,))
        
        rows = cur.fetchall()
        print(f"Found {len(rows)} models for client_id: {client_id}")  # Debug log
        
        models = []
        for row in rows:
            model = {
                "model_id": str(row[0]),
                "client_id": row[1],
                "model_name": row[2],
                "provider_name": row[3],
                "weights_location": row[4],
                "bias_notes": row[5],
                "description": row[6],
                "industry_use_case": row[7],
                "data_store_types": row[8],
                "compliance_requirements": row[9],
                "created_at": row[10].isoformat() if row[10] else None
            }
            models.append(model)
            print(f"Model: {model['model_name']}, Industry: {model['industry_use_case']}, Data Stores: {model['data_store_types']}")  # Debug log
        
        return {"models": models}
    except Exception as e:
        print(f"Error in list_models: {str(e)}")  # Debug log
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@router.delete("/delete/{model_id}")
def delete_model(model_id: UUID):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("DELETE FROM model_inventory WHERE model_id = %s", (str(model_id),))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Model not found")
        conn.commit()
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()