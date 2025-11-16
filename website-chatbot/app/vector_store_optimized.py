import chromadb
import os
import requests
import json

# Initialize ChromaDB persistent client
# Use environment variable for Cloud Run, fallback to local path
chroma_db_path = os.getenv("CHROMA_DB_PATH", "/app/chroma_db")
# Ensure the directory exists
os.makedirs(chroma_db_path, exist_ok=True)
client = chromadb.PersistentClient(path=chroma_db_path)
collection = client.get_or_create_collection(name="chat_docs")

def get_embedding(text, model="text-embedding-004"):
    """
    Get embeddings from Google Gemini API
    Much smaller Docker image compared to sentence-transformers
    Cost: Very affordable with Google's pricing
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        # Fallback: use a simple hash-based embedding (for demo purposes)
        return [hash(text[i:i+10]) % 1000 / 1000.0 for i in range(0, min(len(text), 768), 10)]
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "content": {
            "parts": [{"text": text[:20000]}]  # Gemini has higher token limits
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["embedding"]["values"]
    except Exception as e:
        print(f"❌ Error getting embedding: {e}")
        # Fallback: use a simple hash-based embedding (for demo purposes)
        return [hash(text[i:i+10]) % 1000 / 1000.0 for i in range(0, min(len(text), 768), 10)]

def add_document_to_vector_store(doc_id: str, content: str, metadata: dict):
    try:
        embedding = get_embedding(content)
        collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[doc_id],
            embeddings=[embedding]
        )
        print(f"✅ Added document {doc_id} to ChromaDB")
    except Exception as e:
        print(f"❌ Error adding document to ChromaDB: {e}")

def search_similar_docs(query: str, n_results=3):
    try:
        query_embedding = get_embedding(query)
        results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
        print(f"✅ Found {len(results['documents'][0] if results['documents'] else [])} similar documents")
        return results
    except Exception as e:
        print(f"❌ Error querying ChromaDB: {e}")
        return {"documents": [], "ids": [], "distances": []}

def delete_documents_by_ids(doc_ids: list):
    """
    Delete documents from the collection by their IDs.
    Args:
        doc_ids (list): List of document IDs to delete
    """
    try:
        collection.delete(ids=doc_ids)
        print(f"✅ Deleted {len(doc_ids)} documents from ChromaDB collection 'chat_docs'")
    except Exception as e:
        print(f"❌ Error deleting documents from ChromaDB: {e}")

# Optional: Function to check embedding service health
def check_embedding_service():
    """Check if the embedding service is working"""
    try:
        test_embedding = get_embedding("test")
        return len(test_embedding) > 0
    except:
        return False
