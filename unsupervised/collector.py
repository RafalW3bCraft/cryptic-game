#!/usr/bin/env python3
# Collect logs, reports, and AI history into a deduped raw JSONL dataset.
# Designed for TheFool lab. Runs offline inside the lab.

import os, glob, json, hashlib, argparse, time
from datetime import datetime

DEFAULT_SOURCES = [
    "zeek/logs",           # Zeek outputs (http.log etc)
    "suricata/log",        # Suricata alerts (json/evt)
    "lab/reports",         # markdown reports
    "ai/history",          # ai prompt/response history if stored
    "mock_llm/logs"        # any mock-llm logs
]

OUT_RAW = "unsupervised/dataset_raw.jsonl"
META_DIR = "unsupervised/storage"

def sha256_text(s: str) -> str:
    h = hashlib.sha256()
    h.update(s.encode("utf-8"))
    return h.hexdigest()

def read_file_text(path):
    try:
        with open(path, "r", errors="ignore", encoding="utf-8") as fh:
            return fh.read()
    except Exception:
        return None

def collect(paths):
    os.makedirs(os.path.dirname(OUT_RAW), exist_ok=True)
    os.makedirs(META_DIR, exist_ok=True)
    seen = set()
    count = 0
    with open(OUT_RAW, "w", encoding="utf-8") as out:
        for base in paths:
            for p in glob.glob(os.path.join(base, "**/*"), recursive=True):
                if os.path.isdir(p):
                    continue
                text = read_file_text(p)
                if not text or len(text.strip()) == 0:
                    continue
                # Trim extremely large files (store metadata only)
                if len(text) > 2000000:
                    text_snippet = text[:20000]
                else:
                    text_snippet = text
                payload = {
                    "source": p,
                    "collected_at": datetime.utcnow().isoformat() + "Z",
                    "text": text_snippet
                }
                # dedupe by hash of text (not filename)
                sid = sha256_text(payload["text"])
                if sid in seen:
                    continue
                seen.add(sid)
                payload["id"] = sid
                out.write(json.dumps(payload, ensure_ascii=False) + "\n")
                count += 1
    print(f"[collector] collected {count} items -> {OUT_RAW}")
    return OUT_RAW

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", nargs="*", help="list of source base dirs", default=DEFAULT_SOURCES)
    args = parser.parse_args()
    collect(args.sources)
