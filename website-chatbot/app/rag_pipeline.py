from .vector_store import search_similar_docs
from .llm_client import ask_llm

def answer_query_with_rag(user_query):
    docs = search_similar_docs(user_query, n_results=3)
    context = "\n".join(doc for doc in docs['documents'][0]) if docs['documents'] else ""
    prompt = f"""Based on the context below, answer the user query in a clear, structured format:

Context:
{context}

Query:
{user_query}

CRITICAL FORMATTING REQUIREMENTS:
- ALWAYS use bullet points (•) for lists and features
- ALWAYS use numbered points (1., 2., 3.) for steps or sequential information
- NEVER write long paragraphs - break everything into bullet points
- Use bold (**text**) for emphasis on key terms
- Keep each bullet point short and clear
- Structure information logically with proper spacing
- Make the response easy to read and scan quickly

EXAMPLE FORMAT:
• **Feature 1**: Brief description
• **Feature 2**: Brief description
• **Feature 3**: Brief description

OR for steps:
1. **Step 1**: Brief description
2. **Step 2**: Brief description
3. **Step 3**: Brief description

Response:"""
    return ask_llm(prompt) 