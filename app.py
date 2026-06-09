import gradio as gr
from ingest import parse_cve_folder
from retriever import embed_and_store, retrieve, get_collection
from generator import generate_response


# ---------------------------------------------------------------------------
# Ingestion — runs once on startup
# ---------------------------------------------------------------------------

def run_ingestion():
    """
    Load CVE/NVD advisory documents, chunk them, and store in ChromaDB.

    If the vector store is already populated, ingestion is skipped.
    To re-ingest (e.g. after changing your chunking strategy), delete the
    ./chroma_db folder and restart the app.
    """
    collection = get_collection()

    if collection.count() > 0:
        print(f"Vector store already populated ({collection.count()} chunks). Skipping ingestion.")
        print("To re-ingest, delete the ./chroma_db folder and restart.")
        return

    print("Ingesting vulnerability advisories...")
    cve_chunks = parse_cve_folder()
    print(f"Ingestion complete. {len(cve_chunks)} CVE chunks parsed.")

    if cve_chunks:
        embed_and_store(cve_chunks)
        print(f"Embedding complete. {len(cve_chunks)} chunks stored.")
    else:
        print(
            "\n⚠️  No chunks produced. Make sure parse_cve_folder() is implemented in ingest.py.\n"
            "    VulnBot will start, but won't be able to answer questions yet.\n"
        )


# ---------------------------------------------------------------------------
# Chat handler
# ---------------------------------------------------------------------------

def chat(message, history):
    if not message.strip():
        return ""
    retrieved = retrieve(message)
    return generate_response(message, retrieved)


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

with gr.Blocks(
    theme=gr.themes.Soft(primary_hue="indigo"),
    title="VulnBot",
) as demo:

    gr.HTML("""
        <div style="text-align:center; padding:1.25rem 0 0.5rem;">
            <h1 style="font-size:2rem; font-weight:700; color:#312e81; margin:0;">
                🛡️ VulnBot
            </h1>
            <p style="color:#6b7280; font-size:1rem; margin:0.4rem 0 0;">
                Ask anything about vulnerabilities — answers grounded in CVE/NVD advisories.
            </p>
        </div>
    """)

    with gr.Row():
        with gr.Column(scale=3):
            gr.ChatInterface(
                fn=chat,
                type="messages",
                chatbot=gr.Chatbot(
                    height=440,
                    type="messages",
                    placeholder=(
                        "<div style='text-align:center; color:#9ca3af; margin-top:3rem;'>"
                        "Ask a vulnerability question to get started — grounded in CVE/NVD data 🔐"
                        "</div>"
                    ),
                ),
                textbox=gr.Textbox(
                    placeholder='e.g. "Does Android 16 have a CVE related to app pinning bypass?"',
                    container=False,
                    scale=7,
                ),
                examples=[
                    "What is CVE-2026-0005?",
                    "Show me vulnerabilities affecting OpenSSL 3.0.2.",
                    "Which CVEs are related to CWE-200?",
                    "What is the CVSS score for CVE-2026-0005?",
                    "List recent Google Android advisories.",
                    "Are there any privilege escalation vulnerabilities in Linux kernel 6.x?",
                    "Which CVEs have severity HIGH and vendor Microsoft?",
                ],
                cache_examples=False,
            )

        with gr.Column(scale=1, min_width=180):
            gr.HTML("""
                <div style="background:#f5f3ff; border:1px solid #ddd6fe;
                            border-radius:10px; padding:1rem; margin-top:0.5rem;">
                    <p style="font-size:0.8rem; font-weight:700; color:#4c1d95;
                               margin:0 0 0.5rem; letter-spacing:0.05em;">
                        📚 LOADED SOURCES
                    </p>
                    <ul style="font-size:0.85rem; color:#5b21b6; list-style:none;
                                padding:0; margin:0; line-height:1.8;">
                        <li>🛡️ CVE Database</li>
                        <li>📊 NVD (National Vulnerability Database)</li>
                        <li>🏷️ CWE Weakness Catalog</li>
                        <li>🏢 Vendor Advisories (Google, Microsoft, Cisco, Red Hat)</li>
                    </ul>
                    <hr style="border:none; border-top:1px solid #ddd6fe; margin:0.75rem 0;">
                    <p style="font-size:0.75rem; color:#7c3aed; margin:0; line-height:1.5;">
                        Answers are grounded in the loaded advisories only. If a vulnerability
                        isn't in the data, VulnBot will say so.
                    </p>
                </div>
            """)


if __name__ == "__main__":
    print("\n" + "="*50)
    print("  Vulnerability Vector Database — starting up")
    print("="*50 + "\n")
    run_ingestion()
    demo.launch()
