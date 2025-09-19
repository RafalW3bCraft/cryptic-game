# ai/run.py
# Lightweight FastAPI wrapper exposing /ai/run for inference
import os
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import uvicorn
from ai.engine import AIEngine
from ai.tutor import tutor
from ai.rag_index import RAGIndex



API_KEY = os.environ.get("THEFOOL_AI_API_KEY", "local-dev-key")
BIND_HOST = os.environ.get("THEFOOL_BIND_HOST", "127.0.0.1")
BIND_PORT = int(os.environ.get("THEFOOL_BIND_PORT", "9200"))

app = FastAPI(title="TheFool AI inference (lab-only)")

_engine = AIEngine(model_id=os.environ.get("THEFOOL_MODEL_ID"), load_in_8bit=os.environ.get("THEFOOL_LOAD_8BIT","true").lower()!="false")

class RunReq(BaseModel):
    prompt: str
    max_new_tokens: int = 256
    temperature: float = 0.2
    do_sample: bool = True

rag = RAGIndex()

@app.get("/ai/status")
async def status():
    return {"status": "ok", "mode": _engine.mode, "model_id": _engine.model_id, "loaded": _engine._loaded}

@app.post("/ai/run")
async def run(req: RunReq, request: Request):
    key = request.headers.get("x-api-key","")
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")
    # safety: limit prompt length
    if len(req.prompt) > 20000:
        raise HTTPException(status_code=400, detail="prompt too long")
    result = _engine.generate(req.prompt, max_new_tokens=req.max_new_tokens, temperature=req.temperature, do_sample=req.do_sample)
    return result

@app.post("/ai/tutor")
async def ai_tutor(payload: dict, request: Request):
    key = request.headers.get("x-api-key","")
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")
    stage_id = payload.get("stage_id")
    context = payload.get("context","")
    try:
        out = tutor(stage_id, context)
        return out
    except KeyError:
        raise HTTPException(status_code=400, detail="unknown stage_id")

@app.post("/ai/chat")
async def chat(payload: dict, request: Request):
    key = request.headers.get("x-api-key","")
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")
    query = payload.get("query","")
    top_k = int(payload.get("top_k", 4))
    if not query:
        raise HTTPException(status_code=400, detail="missing query")
    # ensure index exists
    try:
        retrieved = rag.search(query, k=top_k)
    except Exception:
        # fallback: try to build from docs
        try:
            import ai.index_docs as index_docs
            index_docs.main()
            retrieved = rag.search(query, k=top_k)
        except Exception as e:
            retrieved = []
    # build prompt with sources
    context = "\n\n".join([f"Source: {r['id']}\\n{r['text'][:800]}" for r in retrieved])
    prompt = f"You're TheFool lab assistant. Use only the context to answer. Cite sources in square brackets like [ROE.md]. Context:\\n{context}\\n\\nQuery:\\n{query}\\n\\nAnswer concisely and cite sources."
    # use engine
    result = _engine.generate(prompt, max_new_tokens=300, temperature=0.2)
    return {"answer": result, "retrieved": retrieved}


if __name__ == "__main__":
    # lazy-load: do not load model until first request, but we still allow a one-shot load flag
    if os.environ.get("THEFOOL_PRELOAD","false").lower() == "true":
        _engine.load()
    uvicorn.run(app, host=BIND_HOST, port=BIND_PORT)
