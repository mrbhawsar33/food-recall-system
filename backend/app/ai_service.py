import ollama

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

    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]