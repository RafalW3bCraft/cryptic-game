FROM python:3.11-slim
LABEL maintainer="RafalW3bCraft"

RUN apt-get update && apt-get install -y --no-install-recommends build-essential git curl ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ./ai /app/ai
COPY ./requirements-ai.txt /app/requirements-ai.txt

RUN python -m pip install --upgrade pip
RUN pip install -r /app/requirements-ai.txt

EXPOSE 9100
CMD ["python","/app/ai/api.py"]

# Notes:
# - For GPUs: build a CUDA-enabled image and run with --gpus all.
# - For large models, prefer mounting local model weights rather than downloading at build time.
