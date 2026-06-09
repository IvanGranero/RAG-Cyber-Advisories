# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
     Cybersecurity Vulnerabilities and advisories

     Why is this knowledge valuable, and why is it hard to find through official channels?
     Common Vulnerabilities and Exposures databases (CVEs) are searchable by ID or specific keyword only, and considering that CVEs follow a consistent format (ID, description, severity, references), but the descriptions vary widely across vulnerabilities — from buffer overflows to misconfigurations. This balance of structure + diversity is perfect for embeddings.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source  | Description | URL or location                           |
|---|-------- |------       |-----------------                          |
| 1 | CVE Org | JSON Bulk   | https://www.cve.org/Downloads             |
| 2 | NIST    | JSON Bulk   | https://nvd.nist.gov/vulndata-feeds       |
| 3 | CWE     | XML Bulk    | https://cwe.mitre.org/data/downloads.html |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**
Variable size chunk, I will parse each Vulnerability entry and embed as a single chunk.

**Overlap:**
No overlap

**Reasoning:**
Embed the description field directly (usually 1–3 sentences).
Attach metadata separately (CVSS, CWE, CPE, vendor).

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
Main reason due to cost and it is a good baseline model for CVE/NVD text.

**Top-k:**
4

**Production tradeoff reflection:**
I would also try CyberBERT since it is fine-tuned on scientific cybersecurity corpora.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What is CVE‑2026‑0005? | Advisory describing Android app pinning bypass, CVSS 6.2, CWE‑200
| 2 | Show me vulnerabilities affecting OpenSSL 3.0.2 | CVEs describing buffer overflow in OpenSSL handshake | 
| 3 | Are there privilege escalation vulnerabilities in Linux kernel 6.x? | CVEs describing privilege escalation in Linux kernel 6.x. | 
| 4 | CVEs describing denial‑of‑service in Apache HTTP Server | Returned advisories with vendor=Apache, product=HTTP Server | 
| 5 | CVE-2026-0123 | The severity of CVE-2026-0123 is HIGH | 

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.Inconsistent advisory formatting  
CVE and NVD feeds vary in structure and verbosity — some advisories contain rich metadata while others only have a short description. This inconsistency can lead to uneven embeddings and retrieval mismatches, where short advisories are under‑represented or semantically diluted compared to longer ones.

2.Off‑topic semantic retrieval  
Embedding models may over‑prioritize lexical similarity instead of domain relevance, returning advisories that share phrasing but not meaning. For example, “buffer overflow” queries might surface unrelated “stack exhaustion” entries due to shared terminology.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

┌────────────────────────────┐
│        Data Ingestion       │
│────────────────────────────│
│ • Parse CVE / NVD / CWE feeds│
│ • Extract metadata (vendor,  │
│   product, severity, CVSS, CWE)│
└──────────────┬─────────────┘
│
▼
┌────────────────────────────┐
│      Vector Database        │
│────────────────────────────│
│ • Store chunks in ChromaDB  │
│ • Generate embeddings (MiniLM)│
│ • Maintain ID index (CVE IDs) │
└──────────────┬─────────────┘
│
▼
┌────────────────────────────┐
│      Hybrid Retrieval       │
│────────────────────────────│
│ • Exact CVE ID lookup       │
│ • Semantic search for text  │
│ • Metadata filtering (vendor│
│   severity, CWE)            │
└──────────────┬─────────────┘
│
▼
┌────────────────────────────┐
│    Response Generation      │
│────────────────────────────│
│ • Grounded LLM answer       │
│ • Source attribution shown  │
│ • “Not covered” fallback     │
└────────────────────────────┘

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
Tool: Copilot (and occasionally Claude for code scaffolding).

Input: I’ll provide the Chunking Strategy section from planning.md, including the “one CVE = one chunk” rule and metadata flattening requirements.

Expected output: A Python function (parse_cve_folder and chunk_document) that parses CVE/NVD JSON feeds, extracts advisory text, and attaches metadata (vendor, product, severity, CVSS, CWE).

Verification: I’ll run ingestion on a small sample feed and confirm that the output matches the spec: each CVE is a single chunk, metadata is flattened, and the chunk count aligns with the feed size.


**Milestone 4 — Embedding and retrieval:**
Tool: Copilot for code generation, with ChatGPT for hybrid retrieval design.

Input: I’ll provide the Embedding Model and Grounded Generation sections from planning.md, plus the requirement to support hybrid search (semantic + exact CVE ID lookup).

Expected output: An embed_and_store function that batches embeddings into ChromaDB, and a retrieve function that first checks for CVE ID patterns, then falls back to semantic search.

Verification: I’ll test queries like “What is CVE‑2026‑0005?” (ID lookup) and “Privilege escalation in Linux kernel” (semantic search). Correct retrieval will show both advisory text and metadata attribution.

**Milestone 5 — Generation and interface:**
Tool: Copilot for prompt design and Gradio UI scaffolding.

Input: I’ll provide the Grounded Generation section from planning.md, including the system prompt: “Answer ONLY using the provided advisory text. Always state which vendor/product the answer comes from.”

Expected output: A generate_response function that formats retrieved chunks into a context block for the LLM, plus a Gradio ChatInterface that surfaces answers with source attribution.

Verification: I’ll check that responses always cite vendor/product and CVSS metadata, and that off‑topic queries return “The advisories do not cover this question.” I’ll also confirm the UI examples work as expected.