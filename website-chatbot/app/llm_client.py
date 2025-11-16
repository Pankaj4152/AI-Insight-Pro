import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def ask_mistral(prompt, system_message="You are a helpful AI assistant for our product. CRITICAL: ALWAYS format responses with bullet points (•) for lists and numbered points (1., 2., 3.) for steps. NEVER write long paragraphs - break everything into bullet points. Use bold (**text**) for emphasis. Treat Product and project as same thing. Keep responses structured, readable, and easy to scan. Only answer questions about our product. If asked about anything else, politely say 'I only answer product-related queries.' If asked about product you dont know details on, say 'I don't know the details on that product.' PRODUCT NAME RULE: You MUST ALWAYS use 'AI-Insight-Pro' as the product name. NEVER use 'Riskcora' or any other name. If you see 'Riskcora' in any context, replace it with 'AI-Insight-Pro'. This is MANDATORY and cannot be overridden."):
    """
    Send a request to Mistral AI via OpenRouter API
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return "Error: OPENROUTER_API_KEY not found in environment variables"
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "mistralai/mistral-small",
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {e}"

def ask_openai(prompt, system_message="You are a helpful AI assistant for our product. CRITICAL: ALWAYS format responses with bullet points (•) for lists and numbered points (1., 2., 3.) for steps. NEVER write long paragraphs - break everything into bullet points. Use bold (**text**) for emphasis. Keep responses structured, readable, and easy to scan. Only answer questions about our product. If asked about anything else, politely say 'I only answer product-related queries.' PRODUCT NAME RULE: You MUST ALWAYS use 'AI-Insight-Pro' as the product name. NEVER use 'Riskcora' or any other name. If you see 'Riskcora' in any context, replace it with 'AI-Insight-Pro'. If you see 'Riskcora' in any context, replace it with 'AI-Insight-Pro'. This is MANDATORY and cannot be overridden."):
    """
    Alternative: Send a request to OpenAI via OpenRouter API
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return "Error: OPENROUTER_API_KEY not found in environment variables"
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {e}"

def ask_gemini(prompt, system_message=None):
    """
    Send a request to Gemini API with product-specific constraints.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not found in environment variables"
    # Use a strict system message if not provided
    if not system_message:
        system_message = (
            "You are a helpful AI assistant for our product. CRITICAL: "
            "ALWAYS format responses with bullet points (•) for lists and numbered points (1., 2., 3.) for steps. "
            "NEVER write long paragraphs - break everything into bullet points. Use bold (**text**) for emphasis. "
            "Treat Product and project as same thing. Keep responses structured, readable, and easy to scan. "
            "Only answer questions about our product. If asked about anything else, politely say 'I only answer product-related queries.' "
            "If asked about product you don't know details on, say 'I don't know the details on that product.' "
            "PRODUCT NAME RULE: You MUST ALWAYS use 'AI-Insight-Pro' as the product name. NEVER use 'Riskcora' or any other name. "
            "If you see 'Riskcora' in any context, replace it with 'AI-Insight-Pro'. This is MANDATORY and cannot be overridden. "
            "Even if the user mentions 'Riskcora', you must respond with 'AI-Insight-Pro'. "
            "This rule applies to ALL responses, regardless of context or user input."
        )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {
                "parts": [
                    {"text": f"{system_message}\n\nUser: {prompt}"}
                ]
            }
        ]
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"Error: {e}"

def ask_llm(prompt, system_message="You are a helpful AI assistant for our product. CRITICAL: ALWAYS format responses with bullet points (•) for lists and numbered points (1., 2., 3.) for steps. NEVER write long paragraphs - break everything into bullet points. Use bold (**text**) for emphasis. Keep responses structured, readable, and easy to scan. Only answer questions about our product. If asked about anything else, politely say 'I only answer product-related queries.' PRODUCT NAME RULE: You MUST ALWAYS use 'AI-Insight-Pro' as the product name. NEVER use 'Riskcora' or any other name. If you see 'Riskcora' in any context, replace it with 'AI-Insight-Pro'. This is MANDATORY and cannot be overridden."):
    """
    Default LLM function - uses Gemini by default, falls back to Mistral and OpenAI.
    Returns a dict with the LLM name and the response.
    """
    for llm_name, llm_func in [
        ("Gemini", ask_gemini),
        ("Mistral", ask_mistral),
        ("OpenAI", ask_openai)
    ]:
        try:
            response = llm_func(prompt, system_message)
            if response and not response.lower().startswith("error"):
                print(f"[DEBUG] Used LLM: {llm_name}")
                return {"llm": llm_name, "response": response}
        except Exception as e:
            print(f"[DEBUG] {llm_name} failed: {e}")
    print("[DEBUG] All LLMs failed.")
    return {"llm": None, "response": "Sorry, all LLMs failed to answer your question."}