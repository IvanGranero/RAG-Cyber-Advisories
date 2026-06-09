import os
import json
import uuid

def parse_cve_folder(root_path="resources/2026"):
    """
    Recursively traverse all folders inside resources/2026 and parse JSON files
    into chunks suitable for embed_and_store().
    """
    chunks = []

    for dirpath, _, filenames in os.walk(root_path):
        for filename in filenames:
            if not filename.endswith(".json"):
                continue

            file_path = os.path.join(dirpath, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    print(f"Skipping invalid JSON: {file_path}")
                    continue

            # Extract CVE ID
            cve_id = data.get("cveMetadata", {}).get("cveId", None)

            # Extract description (English only)
            descriptions = (
                data.get("containers", {})
                .get("cna", {})
                .get("descriptions", [])
            )
            text = None
            for desc in descriptions:
                if desc.get("lang") == "en":
                    text = desc.get("value")
                    break

            if not text:
                continue  # skip if no usable description

            # Extract metadata (vendor, product, severity, CWE, CVSS)
            affected = (
                data.get("containers", {})
                .get("cna", {})
                .get("affected", [])
            )
            vendor = None
            product = None
            if affected:
                vendor = affected[0].get("vendor")
                product = affected[0].get("product")

            # CVSS score if available
            metrics = (
                data.get("containers", {})
                .get("adp", [{}])[0]
                .get("metrics", [])
            )
            cvss_score = None
            severity = None
            cwe = None
            if metrics:
                cvss = metrics[0].get("cvssV3_1", {})
                cvss_score = cvss.get("baseScore")
                severity = cvss.get("baseSeverity")

                # CWE mapping
                problem_types = (
                    data.get("containers", {})
                    .get("adp", [{}])[0]
                    .get("problemTypes", [])
                )
                if problem_types:
                    cwe = problem_types[0]["descriptions"][0].get("cweId")

            # Build chunk
            chunk = {
                "chunk_id": cve_id or str(uuid.uuid4()),
                "text": text,
                "game": vendor or "unknown",  # mapped to "game" for compatibility
                "metadata": {
                    "product": product,
                    "severity": severity,
                    "cvss": cvss_score,
                    "cwe": cwe,
                },
            }
            chunks.append(chunk)

    return chunks

