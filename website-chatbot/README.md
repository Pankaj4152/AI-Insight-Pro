# LLM-Powered Risk Chatbot (OpenRouter + ChromaDB)
Overview
This chatbot answers both general and client-specific questions about your product's risk analysis and database structure. It uses Mistral via OpenRouter for LLM responses and ChromaDB for retrieval-augmented generation (RAG).

General Qs: "What is risk scoring?", "How does this platform work?"
Client-specific: "How is risk calculated for my data?", "What are my SDEs?"

Stack

Backend: FastAPI
LLM: Mistral via OpenRouter
RAG: ChromaDB
Embedding Model: all-MiniLM-L6-v2
Frontend (optional): React or static HTML/JS

## Folder Structure
```
chatbot/
│
├── app/
│   ├── main.py                   # FastAPI app entry
│   ├── router.py                 # API routes for chatbot
│   ├── llm_client.py             # Wrapper for Mistral/OpenRouter
│   ├── vector_store.py           # ChromaDB operations
│   ├── rag_pipeline.py           # Combines vector + LLM for final answer
│   ├── load_files_to_chromadb.py # Script to load files into ChromaDB
│
├── data/
│   ├── product_docs/             # Markdown/CSV/TXT files with product info
│   ├── client_knowledgebase/     # Client-specific knowledge (optional)
│
├── .env                          # Contains API_KEY
├── requirements.txt              # All dependencies
└── README.md

```
.env Example
OPENROUTER_API_KEY=your_openrouter_key_here

## Setup

Install dependencies:pip install -r requirements.txt


Create a requirements.txt with:fastapi
uvicorn
chromadb
sentence-transformers
mistralai
python-dotenv
markdown


## Start the FastAPI app:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload


Query the Chatbot:Send a POST request to /api/chat with:
{ "query": "How does your platform calculate risk?" }



## Example Questions

"How does your platform calculate risk?"
"What is an SDE?"
"What is the client-specific data score for Company X?"

Notes

The load_files_to_chromadb.py script supports CSV, Markdown, and TXT files.
Mistral will answer anything unless guided. Use system prompts to restrict scope.
For chat history, extend input/output handling with chat memory (in memory or vector-based).

Enhancements

Add chat history/memory
Add user authentication for client-specific queries
Add a React or HTML/JS frontend for live chat
