# Template to fine-tune a causal LM using PEFT/LoRA + Hugging Face Trainer.
# Use only in the lab with controlled datasets.

import os
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments, DataCollatorForLanguageModeling

try:
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
except Exception:
    raise RuntimeError("Install 'peft' to use this script.")

MODEL_ID = os.environ.get("THEFOOL_MODEL_ID", "mistralai/mistral-7b")
OUTPUT_DIR = os.environ.get("THEFOOL_OUTPUT_DIR", "./ai/adapter_out")
TRAIN_FILE = os.environ.get("THEFOOL_TRAIN", "./ai/data/train.jsonl")
VAL_FILE = os.environ.get("THEFOOL_VAL", "./ai/data/val.jsonl")

def main():
    # Load small JSONL-based dataset (each line: {"text": "..."} )
    data_files = {}
    if os.path.exists(TRAIN_FILE):
        data_files['train'] = TRAIN_FILE
    if os.path.exists(VAL_FILE):
        data_files['validation'] = VAL_FILE
    if not data_files:
        raise RuntimeError("No training files found. Put JSONL files at ai/data/*.jsonl")

    ds = load_dataset('json', data_files=data_files)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)

    def tokenize(examples):
        return tokenizer(examples['text'], truncation=True, max_length=1024)

    tokenized = ds.map(tokenize, batched=True, remove_columns=ds[list(ds.keys())[0]].column_names)
    tokenized.set_format(type='torch')

    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, device_map='auto', load_in_8bit=True)
    model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(r=8, lora_alpha=16, target_modules=['q_proj','v_proj'], lora_dropout=0.05, bias='none')
    model = get_peft_model(model, lora_config)

    data_collator = DataCollatorForLanguageModeling(tokenizer, mlm=False)
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        num_train_epochs=1,
        learning_rate=2e-4,
        fp16=True,
        logging_steps=20,
        save_total_limit=2
    )
    trainer = Trainer(model=model, args=training_args, train_dataset=tokenized['train'], eval_dataset=tokenized.get('validation'), data_collator=data_collator)
    trainer.train()
    model.save_pretrained(OUTPUT_DIR)
    print("LoRA adapter saved to", OUTPUT_DIR)

if __name__ == '__main__':
    main()
