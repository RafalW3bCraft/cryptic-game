# FastAPI wrapper for AI Engine + RAG. Lab-only service.

import os, threading
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from ai.engine import AIEngine
from ai.rag_index import RAGIndex

API_KEY = os.environ.get('THEFOOL_AI_API_KEY', 'local-dev-key')
MODEL_ID = os.environ.get('THEFOOL_MODEL_ID', 'mistralai/mistral-7b')

app = FastAPI(title='TheFool AI Service (lab-only)')
engine = AIEngine(model_id=MODEL_ID, load_in_8bit=True)
_model_loaded = False
rag = RAGIndex()

class GenRequest(BaseModel):
    prompt: str
    max_new_tokens: int = 256
    temperature: float = 0.2

class IndexDocsReq(BaseModel):
    docs: list

class ChatReq(BaseModel):
    query: str
    top_k: int = 4

def ensure_loaded():
    global _model_loaded
    if not _model_loaded:
        engine.load()
        _model_loaded = True

@app.post('/generate')
async def generate(req: GenRequest, request: Request):
    key = request.headers.get('x-api-key','')
    if key != API_KEY:
        raise HTTPException(status_code=401, detail='invalid api key')
    try:
        ensure_loaded()
        out = engine.generate(req.prompt, max_new_tokens=req.max_new_tokens, temperature=req.temperature)
        return {'result': out}
    except Exception as e:
        return {'error': str(e)}

@app.post('/index_docs')
async def index_docs(req: IndexDocsReq, request: Request):
    key = request.headers.get('x-api-key','')
    if key != API_KEY:
        raise HTTPException(status_code=401, detail='invalid api key')
    rag.build(req.docs)
    return {'status':'ok','docs_indexed': len(req.docs)}

@app.post('/chat')
async def chat(req: ChatReq, request: Request):
    key = request.headers.get('x-api-key','')
    if key != API_KEY:
        raise HTTPException(status_code=401, detail='invalid api key')
    try:
        hits = rag.search(req.query, k=req.top_k)
        context = "\n\n".join([f"Source: {h['id']}\n{h['text'][:800]}" for h in hits])
        prompt = f"You are a defensive security assistant. Use the context to answer.\n\nContext:\n{context}\n\nQuery:\n{req.query}\n\nAnswer:"
        ensure_loaded()
        out = engine.generate(prompt, max_new_tokens=256, temperature=0.2)
        return {'answer': out, 'retrieved': hits}
    except Exception as e:
        return {'error': str(e)}

def _background_train():
    # tighten this to call containerized job or a controlled training runner
    os.system('python ai/train_lora.py')

@app.post('/train_lora')
async def train_lora(request: Request):
    key = request.headers.get('x-api-key','')
    if key != API_KEY:
        raise HTTPException(status_code=401, detail='invalid api key')
    t = threading.Thread(target=_background_train, daemon=True)
    t.start()
    return {'status':'training_started'}
