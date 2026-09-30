"""Export a minimal, PII-free trace index for the lab's recorded requests."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import httpx
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "submission" / "evidence"
WORKLOAD_FILES = {
    "baseline": EVIDENCE / "07-prompt-baseline-workload.txt",
    "candidate": EVIDENCE / "08-prompt-candidate-workload.txt",
    "practice_rag_slow": EVIDENCE / "17-live-practice-workload.txt",
}
SINGLE_FILES = {
    "promoted_v2": EVIDENCE / "09-production-v2-request.json",
    "rollback_v1": EVIDENCE / "10-rollback-v1-request.json",
}
FIELDS = "core,basic,metadata,prompt,usage,metrics,trace_context"
METADATA_KEYS = ("correlation_id", "prompt_source", "prompt_name", "prompt_label", "prompt_version", "prompt_fetch_error", "feature", "model", "doc_count", "latency_ms", "ttft_ms")


def request_groups() -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for name, path in WORKLOAD_FILES.items():
        raw = path.read_bytes()
        encoding = "utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
        groups[name] = re.findall(r"req-[0-9a-f]{8}", raw.decode(encoding))
    for name, path in SINGLE_FILES.items():
        groups[name] = [json.loads(path.read_text(encoding="utf-8-sig"))["correlation_id"]]
    return groups


def fetch_observations() -> list[dict]:
    load_dotenv(ROOT / ".env")
    base_url = os.environ.get("LANGFUSE_BASE_URL", "https://cloud.langfuse.com").rstrip("/")
    auth = (os.environ["LANGFUSE_PUBLIC_KEY"], os.environ["LANGFUSE_SECRET_KEY"])
    rows: list[dict] = []
    cursor: str | None = None
    with httpx.Client(auth=auth, timeout=20) as client:
        while True:
            params = {"limit": 1000, "fields": FIELDS}
            if cursor:
                params["cursor"] = cursor
            response = client.get(f"{base_url}/api/public/v2/observations", params=params)
            response.raise_for_status()
            payload = response.json()
            rows.extend(payload["data"])
            cursor = payload["meta"].get("cursor")
            if not cursor:
                break
    return rows


def minimal(row: dict) -> dict:
    metadata = row.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}
    return {
        "trace_id": row["traceId"],
        "observation_id": row["id"],
        "parent_observation_id": row.get("parentObservationId"),
        "type": row["type"],
        "name": row.get("name"),
        "start_time": row["startTime"],
        "latency_seconds": row.get("latency"),
        "prompt_name": row.get("promptName"),
        "prompt_version": row.get("promptVersion"),
        "usage_details": row.get("usageDetails"),
        "total_cost_usd": row.get("totalCost"),
        "metadata": {key: metadata[key] for key in METADATA_KEYS if key in metadata},
    }


def main() -> None:
    groups = request_groups()
    wanted = {request_id for ids in groups.values() for request_id in ids}
    observations = fetch_observations()
    selected = [row for row in observations if (row.get("metadata") or {}).get("correlation_id") in wanted]
    by_id: dict[str, list[dict]] = {request_id: [] for request_id in wanted}
    for row in selected:
        by_id[row["metadata"]["correlation_id"]].append(minimal(row))

    result = {
        "source": "Langfuse public v2 observations API",
        "project": "day13-k4-l3a-2A202602958",
        "groups": {
            group: [
                {"correlation_id": request_id, "observations": by_id[request_id]}
                for request_id in ids
            ]
            for group, ids in groups.items()
        },
    }
    output = EVIDENCE / "14-langfuse-trace-index.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, requests in result["groups"].items():
        roots = [observation for item in requests for observation in item["observations"] if observation["type"] == "AGENT"]
        versions = sorted({str(root["metadata"].get("prompt_version")) for root in roots})
        print(f"{name}: requests={len(requests)} roots={len(roots)} versions={','.join(versions)}")
    print(output)


if __name__ == "__main__":
    main()
