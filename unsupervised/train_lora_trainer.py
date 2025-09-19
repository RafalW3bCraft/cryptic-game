#!/usr/bin/env python3
# Train a LoRA adapter on unsupervised/curated.jsonl
# Produces a small adapter in models/iteration_{NNN}

import os, json, hashlib, argparse, math
from datasets import load_dataset
from transformers import AutoTokenizer, DataCollatorForLanguageModeling, TrainingArguments, Trainer, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

BASE_MODEL = os.environ.get("THEFOOL_MODEL_ID", "mistralai/mistral-7b")
CURATED_FILE = "unsupervised/curated.jsonl"
MODELS_DIR = "models"

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def next_iteration(models_dir=MODELS_DIR):
    os.makedirs(models_dir, exist_ok=True)
    existing = [d for d in os.listdir(models_dir) if d.startswith("iteration_")]
    if not existing:
        return 1
    nums = [int(x.split("_")[1]) for x in existing if x.split("_")[1].isdigit()]
    return max(nums)+1 if nums else 1

def prepare_dataset(curated_path=CURATED_FILE):
    # dataset expects JSON lines, each object: {"meta":{...},"text":"..."}
    ds = load_dataset("json", data_files={"train": curated_path})
    # rename 'text' field (it should already be present nested in record)
    def extract(obj):
        # handle if 'text' is nested under 'text' or 'content'
        text = obj.get("text") or obj.get("content") or obj.get("raw") or ""
        return {"text": text}
    ds = ds["train"].map(lambda x: {"text": x.get("text","")}, remove_columns=ds["train"].column_names)
    return ds

def tokenize_and_group(tokenizer, dataset, block_size=1024):
    def tokenize_fn(examples):
        return tokenizer(examples["text"], truncation=True, max_length=block_size)
    tokenized = dataset.map(tokenize_fn, batched=True, remove_columns=["text"])
    tokenized.set_format(type="torch")
    return tokenized

def train(args):
    ds = prepare_dataset(args.curated)
    print(f"[train] dataset size: {len(ds)}")
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(args.model, load_in_8bit=True, device_map="auto")
    model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        # target_modules=["q_proj","v_proj"],  # adjust based on model topology
        target_modules=["c_attn"],  # GPT2 adjust based on model \
        lora_dropout=0.05,
        bias="none"
    )
    model = get_peft_model(model, lora_config)

    tokenized = tokenize_and_group(tokenizer, ds, block_size=args.block_size)
    data_collator = DataCollatorForLanguageModeling(tokenizer, mlm=False)

    iteration = next_iteration(args.models_dir)
    outdir = os.path.join(args.models_dir, f"iteration_{iteration:03d}")
    os.makedirs(outdir, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=outdir,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        num_train_epochs=args.epochs,
        fp16=True if args.fp16 else False,
        logging_steps=10,
        save_total_limit=2,
        report_to="none"
    )

    trainer = Trainer(model=model, args=training_args, train_dataset=tokenized, data_collator=data_collator, tokenizer=tokenizer)
    trainer.train()
    model.save_pretrained(outdir)
    tokenizer.save_pretrained(outdir)

    # manifest
    ds_hash = sha256_file(args.curated)
    model_manifest = {
        "iteration": iteration,
        "outdir": outdir,
        "dataset": args.curated,
        "dataset_sha256": ds_hash
    }
    manifest_path = os.path.join(outdir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(model_manifest, fh, indent=2)
    print(f"[train] saved adapter to {outdir}, manifest -> {manifest_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--curated", default=CURATED_FILE)
    parser.add_argument("--model", default=BASE_MODEL)
    parser.add_argument("--models_dir", default=MODELS_DIR)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--grad_accum", type=int, default=8)
    parser.add_argument("--block_size", type=int, default=1024)
    parser.add_argument("--fp16", action="store_true")
    args = parser.parse_args()
    train(args)
