# ai/engine.py
# TheFool - AI engine (Mistral-compatible scaffold)
# Author: RafalW3bCraft (adapted)
#
# WARNING: Run only inside TheFool isolated lab. Do not use for unauthorized attacks.
import os
import re
import json
import time
import logging
from typing import Optional, Dict, Any

# Transformers / torch imports (optional at runtime)
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
except Exception:
    torch = None
    AutoTokenizer = None
    AutoModelForCausalLM = None
    pipeline = None

# Optional PEFT imports
try:
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training, PeftModel
except Exception:
    LoraConfig = get_peft_model = prepare_model_for_kbit_training = PeftModel = None

LOG_DIR = os.environ.get("THEFOOL_AI_LOG_DIR", "ai/logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Conservative safety rules (start conservative; extend with a classifier later)
_SAFETY_PATTERNS = [
    r"\b(reverse shell|meterpreter|nc\s+-e|bash -i|chmod\s+777|rm\s+-rf\s+/|curl\s+http://.*\.sh|wget\s+http://.*\.sh|base64\s+-d|eval\(|exec\()", 
    r"\bssh\s+-i\b",
    r"\b(password|api_key|secret|token)[\s:=]"
]
_SAFETY_RE = re.compile("|".join(_SAFETY_PATTERNS), re.IGNORECASE)

logger = logging.getLogger("thefool.ai")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(os.path.join(LOG_DIR, "engine.log"))
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)

def audit_event(event: Dict[str, Any]):
    """Append audit event to JSONL audit log."""
    try:
        p = os.path.join(LOG_DIR, "audit.jsonl")
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.exception("Failed to write audit event: %s", e)

def moderate_text(text: str) -> Dict[str, Any]:
    """Basic moderation. Return dict with ok or blocked + reason."""
    if _SAFETY_RE.search(text):
        return {"ok": False, "reason": "safety_regex_match", "excerpt": _SAFETY_RE.search(text).group(0)}
    # Add other checks here (length, profanity, etc.)
    return {"ok": True}

class AIEngine:
    def __init__(self, model_id: Optional[str] = None, device_map: str = "auto", load_in_8bit: bool = True):
        self.model_id = model_id or os.environ.get("THEFOOL_MODEL_ID", "mistralai/mistral-7b")
        self.device_map = device_map
        self.load_in_8bit = bool(load_in_8bit)
        self.tokenizer = None
        self.model = None
        self.pipe = None
        self.peft_applied = False
        self.mode = os.environ.get("THEFOOL_AI_MODE", "mock")  # 'mock' or 'live'
        self._loaded = False

    def _mock_response(self, prompt: str) -> str:
        # deterministic safe stub for dev/testing
        h = str(abs(hash(prompt)))[:8]
        return f"[MOCK-ANSWER {h}] This is a safe mock response from TheFool AI engine."

    def load(self):
        """Load tokenizer and model. This is lazy-load safe; call in background if desired."""
        if self._loaded:
            return
        if self.mode == "mock":
            logger.info("AIEngine: running in MOCK mode; skipping large model load.")
            self._loaded = True
            return

        if AutoTokenizer is None or AutoModelForCausalLM is None:
            raise RuntimeError("transformers not installed in environment. Install requirements before loading model.")

        logger.info("AIEngine: loading tokenizer for %s", self.model_id)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, use_fast=True)

        logger.info("AIEngine: loading model (8bit=%s, device_map=%s)", self.load_in_8bit, self.device_map)
        try:
            if self.load_in_8bit:
                self.model = AutoModelForCausalLM.from_pretrained(self.model_id, load_in_8bit=True, device_map=self.device_map)
            else:
                self.model = AutoModelForCausalLM.from_pretrained(self.model_id, device_map=self.device_map)
        except Exception as e:
            logger.exception("Model load failed: %s", e)
            raise

        # pipeline for convenience
        device = 0 if torch and torch.cuda.is_available() and self.device_map != "cpu" else -1
        self.pipe = pipeline("text-generation", model=self.model, tokenizer=self.tokenizer, device=device)
        self._loaded = True
        logger.info("AIEngine: model loaded")

    def generate(self, prompt: str, max_new_tokens: int = 256, temperature: float = 0.2, do_sample: bool = True) -> Dict[str, Any]:
        """Generate text and moderate. Returns dict: {blocked:bool, text:, meta:...}"""
        meta = {"prompt_len": len(prompt), "timestamp": int(time.time())}
        audit_event({"event":"generate.request","prompt_snippet":prompt[:800],"meta":meta})
        if self.mode == "mock":
            out = self._mock_response(prompt)
            audit_event({"event":"generate.response","mode":"mock","text_snippet":out[:1000]})
            return {"blocked": False, "text": out, "meta": meta}

        if not self._loaded:
            self.load()

        # generate via pipeline (guard for token limits)
        try:
            result = self.pipe(prompt, max_new_tokens=max_new_tokens, do_sample=do_sample, temperature=temperature)
            text = result[0].get("generated_text","") if isinstance(result, list) else str(result)
        except Exception as e:
            logger.exception("Generation error: %s", e)
            text = "[ERROR] model generation failed."

        # moderate before returning
        mod = moderate_text(text)
        if not mod.get("ok", False):
            audit_event({"event":"generate.blocked","reason":mod.get("reason"),"excerpt":mod.get("excerpt")})
            return {"blocked": True, "reason": mod.get("reason"), "meta": meta}

        audit_event({"event":"generate.response","text_snippet":text[:1000],"meta":meta})
        return {"blocked": False, "text": text, "meta": meta}

    def apply_lora(self, **kwargs):
        if get_peft_model is None:
            raise RuntimeError("peft is not installed")
        if not self._loaded:
            self.load()
        try:
            prepare_model_for_kbit_training(self.model)
        except Exception:
            pass
        config = LoraConfig(**kwargs)
        self.model = get_peft_model(self.model, config)
        self.peft_applied = True
        logger.info("AIEngine: LoRA applied")

    def save_adapter(self, out_dir: str):
        if not self.peft_applied:
            raise RuntimeError("No PEFT adapter applied")
        os.makedirs(out_dir, exist_ok=True)
        self.model.save_pretrained(out_dir)
        logger.info("AIEngine: saved adapter %s", out_dir)

    def load_adapter(self, adapter_dir: str):
        if PeftModel is None:
            raise RuntimeError("peft.PeftModel required to load adapter")
        if not self._loaded:
            self.load()
        self.model = PeftModel.from_pretrained(self.model, adapter_dir)
        self.peft_applied = True
        logger.info("AIEngine: loaded adapter from %s", adapter_dir)
