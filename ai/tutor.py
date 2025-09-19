# TheFool AI tutor helper: returns safe, lab-only guidance per workflow stage.
import os
import yaml
from typing import Dict
import requests

WORKFLOW_FILE = os.environ.get("THEFOOL_WORKFLOW", "workflow/stages.yml")
AI_RUN_URL = os.environ.get("THEFOOL_AI_RUN_URL", "http://127.0.0.1:9200/ai/run")
API_KEY = os.environ.get("THEFOOL_AI_API_KEY", "local-dev-key")

def load_workflow():
    with open(WORKFLOW_FILE, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)

def get_stage(stage_id: str) -> Dict:
    wf = load_workflow()
    for s in wf.get("stages", []):
        if s.get("id") == stage_id:
            return s
    raise KeyError(f"unknown stage {stage_id}")

def safe_prompt_for_stage(stage: Dict, context: str = "") -> str:
    # Build a defensive prompt template that forces the model to produce lab-only guidance.
    p = (
        "You are a defensive security assistant for a sandboxed lab called TheFool. "
        "Always instruct the user to operate only in authorized lab environments, avoid real-world attacks, "
        "and never provide exploit payloads or instructions that could be used against third-party systems. "
        f"Stage name: {stage.get('name')}. Description: {stage.get('description')}. "
        "Produce a clear step-by-step checklist, safe tool suggestions (from allowed tools), and evidence collection advice. "
    )
    if context:
        p += f"Context: {context}. "
    return p

def tutor(stage_id: str, context: str = "") -> Dict:
    stage = get_stage(stage_id)
    result = {"stage": stage_id, "name": stage.get("name"), "checklist": stage.get("checklist"), "advice": None}
    # Try to get AI-extended advice, but only in lab
    try:
        # Query local AI run if available
        payload = {"prompt": safe_prompt_for_stage(stage, context), "max_new_tokens": 256}
        headers = {"x-api-key": API_KEY}
        resp = requests.post(AI_RUN_URL, json=payload, headers=headers, timeout=20)
        data = resp.json()
        if data.get("blocked"):
            result["advice"] = "AI response was blocked by safety filters. Please use checklist and manual guidance."
        else:
            result["advice"] = data.get("text")
    except Exception as e:
        # if AI service not available, return static text
        result["advice"] = (
            "AI assistant unavailable. Follow checklist and ensure all actions are in-scope. "
            "Use devtools, Burp Proxy in lab, capture requests, and submit sanitized evidence."
        )
    return result
