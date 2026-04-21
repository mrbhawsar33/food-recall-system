import ollama

def generate_summary(title: str, category: str) -> str:
    severity = {"1": "high risk", "2": "medium risk", "3": "low risk"}.get(category, "unknown risk")

    prompt = f"""You are a food safety assistant. Given a food recall title and severity, write a 2-sentence plain-language summary for the general public. Be clear and simple.

Recall title: {title}
Severity: {severity}

Write only the 2-sentence summary, nothing else."""

    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]