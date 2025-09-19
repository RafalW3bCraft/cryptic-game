# RAG index helper supporting FAISS (default) and optional Chroma (if configured)
import os, json
from sentence_transformers import SentenceTransformer
import numpy as np

USE_CHROMA = os.environ.get("THEFOOL_USE_CHROMA", "0") == "1"

if USE_CHROMA:
    try:
        import chromadb
        from chromadb.config import Settings
    except Exception:
        chromadb = None

if not USE_CHROMA:
    try:
        import faiss
    except Exception:
        faiss = None

EMBED_MODEL = os.environ.get("THEFOOL_EMBED", "sentence-transformers/all-MiniLM-L6-v2")
INDEX_PATH = os.environ.get("THEFOOL_FAISS_INDEX", "ai/faiss_index.bin")

class RAGIndex:
    def __init__(self, embed_model=EMBED_MODEL):
        self.embedder = SentenceTransformer(embed_model)
        self.index = None
        self.docs = []

    def build(self, docs, index_path=INDEX_PATH):
        texts = [d["text"] for d in docs]
        vecs = self.embedder.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        d = vecs.shape[1]
        if not USE_CHROMA:
            if faiss is None:
                raise RuntimeError("faiss not installed")
            idx = faiss.IndexFlatIP(d)
            faiss.normalize_L2(vecs)
            idx.add(vecs)
            self.index = idx
            self.docs = docs
            faiss.write_index(idx, index_path)
            with open(index_path + ".meta.json", "w", encoding="utf-8") as fh:
                json.dump(self.docs, fh)
        else:
            # chroma usage
            client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory="ai/chroma"))
            collection = client.create_collection(name="thefool", get_or_create=True)
            ids = [d["id"] for d in docs]
            collection.add(ids=ids, metadatas=[d.get("meta",{}) for d in docs], documents=texts, embeddings=vecs.tolist())
            # persist done by chroma client
            self.docs = docs

    def search(self, query, k=4, index_path=INDEX_PATH):
        qv = self.embedder.encode([query], convert_to_numpy=True)
        if not USE_CHROMA:
            if self.index is None:
                self.index = faiss.read_index(index_path)
                with open(index_path + ".meta.json", "r", encoding="utf-8") as fh:
                    self.docs = json.load(fh)
            faiss.normalize_L2(qv)
            D, I = self.index.search(qv, k)
            results = []
            for dist, idx in zip(D[0], I[0]):
                if idx < 0: continue
                doc = self.docs[idx]
                results.append({"score": float(dist), "id": doc["id"], "text": doc["text"], "meta": doc.get("meta", {})})
            return results
        else:
            # Chroma search
            client = chromadb.Client()
            collection = client.get_collection("thefool")
            hits = collection.query(query_embeddings=qv.tolist(), n_results=k)
            results = []
            for i in range(len(hits["ids"][0])):
                idx_id = hits["ids"][0][i]
                score = hits["distances"][0][i] if "distances" in hits else None
                # get the doc from docs list
                for d in self.docs:
                    if d["id"] == idx_id:
                        results.append({"score": score, "id": d["id"], "text": d["text"], "meta": d.get("meta", {})})
                        break
            return results
