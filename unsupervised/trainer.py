from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from datasets import load_dataset
import os

MODEL_NAME = "mistralai/Mistral-7B-v0.1"
DATASET_FILE = "unsupervised/dataset.jsonl"
OUTPUT_DIR = "models/iteration_1"

def train():
    dataset = load_dataset("json", data_files=DATASET_FILE, split="train")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

    def tokenize(batch):
        return tokenizer(batch["text"], padding="max_length", truncation=True, max_length=512)

    dataset = dataset.map(tokenize, batched=True)

    args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        overwrite_output_dir=True,
        num_train_epochs=1,
        per_device_train_batch_size=1,
        save_steps=50,
        save_total_limit=2,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=dataset,
        tokenizer=tokenizer,
    )

    trainer.train()
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"[+] Model fine-tuned and saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    train()
