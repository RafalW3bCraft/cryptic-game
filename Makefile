
# Makefile — TheFool top-level helpers (DVC-aware)
.PHONY: help dvc-init collect curate train iterate snapshot clean

help:
	@echo "Targets: dvc-init, collect, curate, train, iterate, snapshot, clean"
	@echo "Use 'make dvc-init' to initialize DVC (admin)."

dvc-init:
	@echo "[make] Initializing DVC (interactive step)"
	dvc init || echo "dvc init failed or already initialized"
	@echo "Now configure a remote, e.g.:"
	@echo "  dvc remote add -d storage s3://your-bucket/thefool"
	@echo "  dvc remote modify storage access_key_id <id>"
	@echo "  dvc remote modify storage secret_access_key <secret>"

collect:
	@echo "[make] collecting raw data"
ifdef DVC
	dvc repro collect
else
	python3 unsupervised/collector.py
endif

curate:
	@echo "[make] curating dataset"
ifdef DVC
	dvc repro curate
else
	python3 unsupervised/curator.py --raw unsupervised/dataset_raw.jsonl --curated unsupervised/curated.jsonl --review unsupervised/human_review.jsonl
endif

train:
	@echo "[make] training adapter (LoRA)"
ifdef DVC
	dvc repro train
else
	python3 unsupervised/train_lora_trainer.py --curated unsupervised/curated.jsonl --fp16
endif

snapshot:
	@echo "[make] snapshot + manifest"
	python3 unsupervised/manifest_tool.py --sign

iterate: collect curate train snapshot
	@echo "[make] iteration complete"

clean:
	@echo "[make] cleaning artifacts"
	rm -f unsupervised/dataset_raw.jsonl unsupervised/curated.jsonl
