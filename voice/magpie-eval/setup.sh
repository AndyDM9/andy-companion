#!/usr/bin/env bash
# The environment for evaluating NVIDIA Magpie TTS Multilingual 357M beside Andy's current voice
# (PLAN B7). Its own folder and virtual environment, so the running voice server is never touched.
#
#   voice/magpie-eval/setup.sh      then   voice/magpie-eval/.venv/bin/python voice/magpie-eval/evaluate.py
#
# NeMo's model card asks for nemo_toolkit[tts] from its main branch, installed after PyTorch.
set -euo pipefail
cd "$(dirname "$0")"
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python torch torchaudio
uv pip install --python .venv/bin/python "nemo_toolkit[tts] @ git+https://github.com/NVIDIA/NeMo.git@main" kaldialign soundfile peft
echo "Ready: .venv/bin/python evaluate.py"
