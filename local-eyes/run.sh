#!/usr/bin/env bash
# Andy's offline eyes: NVIDIA Cosmos Reason 2 2B, served by vLLM on this computer (decision 0015). Used when
# ANDY_VISION=local, or when Nemotron 3.5 Super VL on Token Factory can't be reached and ANDY_VISION_FALLBACK=local.
# Listens on 127.0.0.1:8095 only, so a picture never leaves this computer. vLLM logs no request text unless
# --enable-log-requests is given, and it isn't.
#
#   local-eyes/run.sh            the first start downloads the model (about 5 GB) from Hugging Face; its licence
#                                must be accepted there first, with this computer's Hugging Face login
set -euo pipefail
cd "$(dirname "$0")"
# GPU 0 unless ANDY_LOCAL_EYES_GPU picks another. The model card asks for a 24 GB GPU; on a computer with one
# GPU, lower ANDY_LOCAL_EYES_MEMORY so the voice server still fits beside it.
export CUDA_VISIBLE_DEVICES="${ANDY_LOCAL_EYES_GPU:-0}"
exec .venv/bin/vllm serve nvidia/Cosmos-Reason2-2B \
  --served-model-name cosmos-reason2 \
  --host 127.0.0.1 --port "${ANDY_LOCAL_EYES_PORT:-8095}" \
  --max-model-len 32768 \
  --limit-mm-per-prompt '{"image": 32}' \
  --gpu-memory-utilization "${ANDY_LOCAL_EYES_MEMORY:-0.6}" \
  --disable-uvicorn-access-log \
  "$@"
