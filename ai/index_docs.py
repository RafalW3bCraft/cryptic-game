#!/usr/bin/env python3
# Build RAG index from TheFool docs (ROE.md, templates, rules, workflow).
import os, json, glob
from ai.rag_index import RAGIndex

DOC_PATHS = [
    "ROE.md",
    "lab/reports/TEMPLATE.md",
    "workflow/stages.yml",
    "suricata/rules/thefool.rules",
]

OUT_INDEX = "ai/faiss_index.bin"

def gather_docs(paths=DOC_PATHS):
    docs = []
    for p in paths:
        if not os.path.exists(p):
            continue
        with open(p, "r", encoding="utf-8", errors="ignore") as fh:
            txt = fh.read()
        docs.append({"id": os.path.basename(p), "text": txt, "meta": {"path": p}})
    # also include files under docs/ or additional directories
    for f in glob.glob("docs/**/*.md", recursive=True):
        with open(f, "r", encoding="utf-8", errors="ignore") as fh:
            docs.append({"id": os.path.relpath(f), "text": fh.read(), "meta": {"path": f}})
    return docs

def main():
    docs = gather_docs(DOC_PATHS)
    if not docs:
        print("No docs found to index.")
        return
    rag = RAGIndex()
    rag.build(docs, index_path=OUT_INDEX)
    print("Indexed docs ->", OUT_INDEX)

if __name__ == "__main__":
    main()
