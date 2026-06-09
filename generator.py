from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL

_client = Groq(api_key=GROQ_API_KEY)

def generate_response(query, retrieved_chunks):
    """
    Generate a grounded answer from retrieved CVE/NVD advisory chunks.

    Each chunk dict has:
      - "text"     : vulnerability description
      - "metadata" : dict with vendor, product, severity, cvss, cwe
      - "distance" : similarity score
    """
    if not retrieved_chunks:
        return (
            "I couldn't find anything relevant in the loaded advisories. "
            "Try rephrasing your question — or check that your ingestion pipeline is working."
        )

    # Optional filter for weak matches
    threshold = 0.4
    filtered = [c for c in retrieved_chunks if c["distance"] <= threshold]
    if not filtered:
        return (
            "I couldn't find anything relevant in the loaded advisories. "
            "Try rephrasing your question — or check that your ingestion pipeline is working."
        )

    # Format context blocks with metadata
    context_blocks = []
    for c in filtered:
        meta = c.get("metadata", {})
        block = (
            f"[Vendor: {meta.get('vendor','unknown')} | "
            f"Product: {meta.get('product','unknown')} | "
            f"Severity: {meta.get('severity','')} | "
            f"CVSS: {meta.get('cvss','')} | "
            f"CWE: {meta.get('cwe','')}]\n"
            f"{c['text']}"
        )
        context_blocks.append(block)
    context = "\n\n".join(context_blocks)

    # Build messages
    messages = [
        {
            "role": "system",
            "content": (
                "You are a cybersecurity advisory assistant. "
                "Answer ONLY using the provided advisory text. "
                "If the advisories do not contain the answer, say clearly that the advisories do not cover it. "
                "Always state which vendor/product the answer comes from."
            ),
        },
        {
            "role": "user",
            "content": f"Question: {query}\n\nRelevant advisories:\n{context}",
        },
    ]

    # Call LLM
    response = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
    )

    return response.choices[0].message.content.strip()
