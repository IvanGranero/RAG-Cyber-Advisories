---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
 -->
Cybersecurity Vulnerabilities and advisories

Common Vulnerabilities and Exposures databases (CVEs) are searchable by ID or specific keyword only, and considering that CVEs follow a consistent format (ID, description, severity, references), but the descriptions vary widely across vulnerabilities — from buffer overflows to misconfigurations. This balance of structure + diversity is perfect for embeddings.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source  | Type      | URL or file path                          |
|---|-------- |------     |-----------------                          |
| 1 | CVE Org | JSON Bulk | https://www.cve.org/Downloads             |
| 2 | NIST    | JSON Bulk | https://nvd.nist.gov/vulndata-feeds       |
| 3 | CWE     | XML Bulk  | https://cwe.mitre.org/data/downloads.html |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunking approach**
Embed the description field directly (usually 1–3 sentences).
Attach metadata separately (CVSS, CWE, CPE, vendor).

**Chunk size:**
Variable size chunk, I will parse each Vulnerability entry and embed as a single chunk.

**Why these choices fit your documents:**
Keeps each advisory intact (CVE description + metadata).
More natural for structured data (CVE entries, API docs, JSON feeds).
Reduces preprocessing complexity — one CVE = one chunk.

**Final chunk count:**
22,626
Note: ChromaDB enforces a maximum batch size of 5,461. Therefore the chunks were stored on a total of 5 batches in ChromaDB.
---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
Main reason due to cost and it is a good baseline model for CVE/NVD text.

**Production tradeoff reflection:**
I would also try CyberBERT since it is fine-tuned on scientific cybersecurity corpora.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**
You are a cybersecurity advisory assistant. 
Answer ONLY using the provided advisory text. 
If the advisories do not contain the answer, say clearly that the advisories do not cover it. 
Always state which vendor/product the answer comes from.


**How source attribution is surfaced in the response:**
The system surfaces attribution by including advisory metadata directly in the response context. Each retrieved chunk is formatted with its vendor, product, severity, CVSS score, and CWE ID before being passed to the LLM. 
---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What is CVE‑2026‑0005? | Advisory describing Android app pinning bypass, CVSS 6.2, CWE‑200 | The advisories do not cover CVE-2026-0005. | Off-target | Innacurate  |
| 2 | Show me vulnerabilities affecting OpenSSL 3.0.2 | CVEs describing buffer overflow in OpenSSL handshake | I couldn't find anything relevant in the loaded advisories. Try rephrasing your question — or check that your ingestion pipeline is working. | Off-target | Innacurate |
| 3 | Are there privilege escalation vulnerabilities in Linux kernel 6.x? | CVEs describing privilege escalation in Linux kernel 6.x. | According to the Linux advisory, yes, there is a potential privilege escalation vulnerability in the Linux kernel ... | Relevant | Accurate  |
| 4 | CVEs describing denial‑of‑service in Apache HTTP Server | Returned advisories with vendor=Apache, product=HTTP Server | The advisory from Apache Software Foundation for Apache HTTP Server describes a denial-of-service vu... | Relevant | Accurate |
| 5 | CVE-2026-0123 | The severity of CVE-2026-0123 is HIGH | The severity of CVE-2026-0123 is HIGH, according to Google for their Android product, with a CVSS score of 8.4. | Relevant | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**
What is CVE‑2026‑0005?

**What the system returned:**
The advisories do not cover CVE-2026-0005.

**Root cause (tied to a specific pipeline stage):**
I am not embedding the CVE ids into the documents

**What you would change to fix it:**
I changed my pure semantic search to a Hybrid search approach

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**
The spec forced me to think carefully about my chunking strategy before writing any code. By committing to “one CVE = one chunk,” I avoided unnecessary complexity and ensured that retrieval would always return atomic advisory units. This decision simplified ingestion and made evaluation more straightforward. The spec also guided me to define grounding instructions early, which meant my system prompt was consistent and prevented hallucinations during generation.

**One way your implementation diverged from the spec, and why:**
The spec originally assumed that semantic search alone would be sufficient. In practice, I diverged by adding a hybrid retrieval path: exact ID lookups for CVEs and semantic search for natural language queries. This was necessary because users often ask “What is CVE‑2026‑0005?” and semantic embeddings don’t capture IDs well. By diverging from the spec, I improved accuracy for ID‑based queries while still supporting flexible natural language search.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
My notes from planning.md about chunking CVE JSON feeds and asked for a reproducible Python function to parse them.

- *What it produced:*
A function using os.listdir() to parse JSON files in a single folder.

- *What I changed or overrode:*
I replaced os.listdir() with os.walk() so the ingestion could handle nested subfolders inside resources/2026, since CVE feeds are organized hierarchically. I also added error handling for invalid JSON files.

**Instance 2**

- *What I gave the AI:*
My old embed_and_store function for board game rules and asked to adapt it for CVE/NVD advisories.

- *What it produced:*
A version that still used game metadata and embedded only the description text.

- *What I changed or overrode:*
I updated the metadata schema to flatten vendor, product, severity, cvss, and cwe, ensuring ChromaDB could serialize them. I also added batching to avoid exceeding ChromaDB’s max batch size and later introduced hybrid retrieval logic so CVE IDs could be looked up directly.
