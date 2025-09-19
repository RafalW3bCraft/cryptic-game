#!/usr/bin/env bash
python3 -m venv .venv-ai
source .venv-ai/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "Virtualenv created and requirements installed. Install GPU-specific torch/bitsandbytes if using GPUs."
