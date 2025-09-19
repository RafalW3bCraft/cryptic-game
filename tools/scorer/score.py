#!/usr/bin/env python3
import glob, re, json, os, datetime

RUBRIC = {
    "Informational": 1,
    "Low": 3,
    "Medium": 5,
    "High": 10,
}
REPORT_DIR = "lab/reports"
OUT = "web/leaderboard.json"

def parse_severity(text):
    m = re.search(r"Severity:.*(Informational|Low|Medium|High)", text, re.IGNORECASE)
    if m:
        return m.group(1).capitalize()
    return None

scores = {}
for path in glob.glob(os.path.join(REPORT_DIR, "*.md")):
    text = open(path, encoding="utf-8").read()
    # crude author parse
    author_m = re.search(r"Author:\s*(.+)", text)
    author = author_m.group(1).strip() if author_m else "unknown"
    sev = parse_severity(text) or "Informational"
    pts = RUBRIC.get(sev, 1)
    bonus = 5 if "Remediation" in text and "Evidence" in text else 0
    scores.setdefault(author, {"points":0, "reports":0})
    scores[author]["points"] += pts + bonus
    scores[author]["reports"] += 1

# build leaderboard list
board = sorted([{"author":a, **d} for a,d in scores.items()], key=lambda x: -x["points"])
out = {"updated": datetime.datetime.utcnow().isoformat()+"Z", "leaderboard": board}
os.makedirs("web", exist_ok=True)
open(OUT,"w",encoding="utf-8").write(json.dumps(out, indent=2))
print("Wrote", OUT)
