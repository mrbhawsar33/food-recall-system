import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemma-3-27b-it:generateContent"

def generate_summary(title: str, recall_class: str) -> str:
    severity = {
        "Class 1": "high risk — may cause serious health consequences or death",
        "Class 2": "moderate risk — may cause temporary health consequences",
        "Class 3": "low risk — unlikely to cause health consequences"
    }.get(recall_class, "unknown risk")

    prompt = f"""You are a food safety assistant. Given a food recall title and severity, write a 2-sentence plain-language summary for the general public. Be clear and simple.

Recall title: {title}
Severity: {severity}

Write only the 2-sentence summary, nothing else."""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = httpx.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json=payload,
            timeout=15
        )
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        return f"This is a {recall_class} recall for {title}. Please follow instructions from the recall notice."