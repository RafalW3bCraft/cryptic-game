#!/usr/bin/env python3
# Curates dataset_raw.jsonl -> curated.jsonl + human_review.jsonl
# - PII redaction (emails, phones, IPs, API keys)
# - Flagging of sensitive/exploit-like content (moved to human review)
# - Basic dedupe retained from collector

import re, json, os, argparse
from datetime import datetime
from typing import Dict

RAW = "unsupervised/dataset_raw.jsonl"
CURATED = "unsupervised/curated.jsonl"
REVIEW = "unsupervised/human_review.jsonl"

# Patterns for redaction and sensitive content
EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?){1,3}\d{2,4}")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
APIKEY_RE = re.compile(r"(?i)(?:api_key|apikey|secret|token|passwd|password)[^\\n\\r\\s:]{0,5}[:=]\\s*([A-Za-z0-9\\-\\._]{8,})")
BASE64_RE = re.compile(r"(?<![A-Za-z0-9+/=])(?:[A-Za-z0-9+/]{40,}={0,2})(?![A-Za-z0-9+/=])")
# Sensitive or exploit-like trigger phrases (conservative)
SENSITIVE_RE = re.compile(r"(reverse shell|meterpreter|nc -e|bash -i|chmod 777|rm -rf /|curl .*sh|wget .*sh|base64 -d|exploit|sqlmap|payload|RCE|ssh -i|msfconsole)", re.IGNORECASE)

def redact(text: str) -> str:
    t = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    t = PHONE_RE.sub("[REDACTED_PHONE]", t)
    t = IP_RE.sub("[REDACTED_IP]", t)
    t = APIKEY_RE.sub("[REDACTED_SECRET]", t)
    t = BASE64_RE.sub("[REDACTED_B64]", t)
    return t

def is_sensitive(text: str) -> bool:
    return bool(SENSITIVE_RE.search(text))

def curate(raw_path=RAW, curated_out=CURATED, review_out=REVIEW):
    os.makedirs(os.path.dirname(curated_out) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(review_out) or ".", exist_ok=True)
    count_in = 0
    count_cur = 0
    count_rev = 0
    with open(raw_path, "r", encoding="utf-8") as inf, \
         open(curated_out, "w", encoding="utf-8") as cout, \
         open(review_out, "w", encoding="utf-8") as rvw:
        for line in inf:
            count_in += 1
            try:
                obj = json.loads(line)
            except Exception:
                continue
            text = obj.get("text","")
            if not text.strip():
                continue
            # redact
            red = redact(text)
            # short metadata
            meta = {
                "id": obj.get("id"),
                "source": obj.get("source"),
                "collected_at": obj.get("collected_at", datetime.utcnow().isoformat() + "Z")
            }
            # If sensitive, push to review queue (do not include in training)
            if is_sensitive(text):
                rvw.write(json.dumps({"meta": meta, "raw_excerpt": text[:2000], "flag": "sensitive", "curated_excerpt": redact(text[:2000])}, ensure_ascii=False) + "\n")
                count_rev += 1
                continue
            # Otherwise write curated record
            rec = {"meta": meta, "text": red}
            cout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            count_cur += 1
    print(f"[curator] in:{count_in} curated:{count_cur} review:{count_rev}")
    return curated_out, review_out

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default=RAW)
    parser.add_argument("--curated", default=CURATED)
    parser.add_argument("--review", default=REVIEW)
    args = parser.parse_args()
    curate(args.raw, args.curated, args.review)
