import chromadb
import csv
import os
import markdown
import glob
import requests
import json
from dotenv import load_dotenv

load_dotenv()

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
        print(f"❌ Error getting embedding for text (length: {len(text)}): {e}")
        # Fallback: use a simple hash-based embedding
        return [hash(text[i:i+10]) % 1000 / 1000.0 for i in range(0, min(len(text), 768), 10)]

def check_chromadb_exists(persist_directory):
    print(f"[DEBUG] Checking ChromaDB persist directory: {persist_directory}")
    if not os.path.exists(persist_directory):
        print(f"❌ ChromaDB persist directory does not exist: {persist_directory}")
        return False
    files = os.listdir(persist_directory)
    if files:
        print(f"✅ ChromaDB vector DB exists at: {persist_directory}")
        print(f"   Files: {files}")
        return True
    else:
        print(f"⚠️ ChromaDB persist directory exists but is empty: {persist_directory}")
        return False

def load_files_to_chromadb(file_patterns, collection_name="chat_docs", persist_directory=None, fields_to_embed=None, clear_existing=False):
    if persist_directory is None:
        persist_directory = os.getenv("CHROMA_DB_PATH", "/app/chroma_db")
    
    # Ensure directory exists
    os.makedirs(persist_directory, exist_ok=True)
    print(f"[DEBUG] Using persist_directory: {os.path.abspath(persist_directory)}")
    check_chromadb_exists(persist_directory)

    # Use PersistentClient for ChromaDB 1.x
    client = chromadb.PersistentClient(path=persist_directory)
    collection = client.get_or_create_collection(collection_name)

    # Test embedding service
    print("🔄 Testing embedding service...")
    try:
        test_embedding = get_embedding("test")
        print(f"✅ Embedding service working. Embedding dimension: {len(test_embedding)}")
    except Exception as e:
        print(f"❌ Error testing embedding service: {e}")
        print("⚠️ Will continue with fallback embeddings...")

    if clear_existing:
        doc_ids_to_delete = []
        for pattern in file_patterns:
            for file_path in glob.glob(pattern):
                file_ext = os.path.splitext(file_path)[1].lower()
                if file_ext == ".csv":
                    try:
                        with open(file_path, newline='', encoding='utf-8') as csvfile:
                            reader = csv.DictReader(csvfile)
                            doc_ids_to_delete.extend([str(row.get("id", f"{file_path}_{i}")) for i, row in enumerate(reader)])
                    except Exception as e:
                        print(f"❌ Error reading CSV file {file_path}: {e}")
                elif file_ext in [".md", ".txt"]:
                    doc_ids_to_delete.append(f"{file_path}_0")
        
        if doc_ids_to_delete:
            try:
                collection.delete(ids=doc_ids_to_delete)
                print(f"✅ Deleted {len(doc_ids_to_delete)} existing documents from ChromaDB")
            except Exception as e:
                print(f"❌ Error deleting existing documents: {e}")

    documents = []
    for pattern in file_patterns:
        for file_path in glob.glob(pattern):
            file_ext = os.path.splitext(file_path)[1].lower()
            try:
                if file_ext == ".csv":
                    with open(file_path, newline='', encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        for row in reader:
                            doc_id = str(row.get("id", f"{file_path}_{len(documents)}"))
                            if fields_to_embed:
                                text = " ".join(str(row.get(field, "")) for field in fields_to_embed)
                            else:
                                text = " ".join(str(value) for value in row.values())
                            documents.append({"id": doc_id, "text": text})
                elif file_ext in [".md", ".txt"]:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()
                        if file_ext == ".md":
                            text = markdown.markdown(content)
                        else:
                            text = content
                        doc_id = f"{file_path}_{len(documents)}"
                        documents.append({"id": doc_id, "text": text})
                else:
                    print(f"⚠️ Unsupported file type: {file_path}")
                    continue
            except Exception as e:
                print(f"❌ Error processing file {file_path}: {e}")
                continue

    if not documents:
        print("No documents found in specified files.")
        return 0

    print(f"🔄 Generating embeddings for {len(documents)} documents...")
    try:
        embeddings = []
        for i, doc in enumerate(documents):
            if i % 5 == 0:  # Progress indicator every 5 documents
                print(f"   Processing document {i+1}/{len(documents)}")
            embedding = get_embedding(doc["text"])
            embeddings.append(embedding)
        print("✅ All embeddings generated successfully")
    except Exception as e:
        print(f"❌ Error generating embeddings: {e}")
        return 0

    try:
        collection.add(
            ids=[doc["id"] for doc in documents],
            documents=[doc["text"] for doc in documents],
            embeddings=embeddings
        )
        print(f"✅ Loaded {len(documents)} documents into ChromaDB collection '{collection_name}'")
        
        # Debug: Check persist directory after loading
        if os.path.exists(persist_directory):
            files = os.listdir(persist_directory)
            print(f"[DEBUG] Files in persist directory after loading: {files}")
        else:
            print(f"[DEBUG] Persist directory does not exist after loading: {persist_directory}")
        return len(documents)
    except Exception as e:
        print(f"❌ Error adding to ChromaDB: {e}")
        return 0

if __name__ == "__main__":
    # Example file patterns - update these to match your data structure
    file_patterns = [
        "data/product_docs/*.md",
        "data/product_docs/*.txt", 
        "data/product_docs/*.csv"
    ]
    
    print("🚀 Starting document loading with API-based embeddings...")
    print("📊 This approach saves ~1GB in Docker image size!")
    
    result = load_files_to_chromadb(
        file_patterns=file_patterns,
        collection_name="chat_docs",
        persist_directory=None,  # Will use CHROMA_DB_PATH env var or default
        clear_existing=True
    )
    print(f"✅ Successfully loaded {result} documents into ChromaDB")
