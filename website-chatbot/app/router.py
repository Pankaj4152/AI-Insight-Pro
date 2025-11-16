from fastapi import APIRouter
from pydantic import BaseModel
from .rag_pipeline import answer_query_with_rag

router = APIRouter()

class ChatRequest(BaseModel):
    query: str

@router.get("/health")
def health_check():
    """Health check endpoint for Cloud Run"""
    return {"status": "healthy", "service": "chatbot"}

@router.post("/chat")
def chat_endpoint(req: ChatRequest):
    llm_result = answer_query_with_rag(req.query)
    # If the result is a dict with llm info, extract the response
    if isinstance(llm_result, dict) and "response" in llm_result:
        return {"response": llm_result["response"], "llm_used": llm_result.get("llm")}
    else:
        return {"response": llm_result}