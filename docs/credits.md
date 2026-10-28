# Licences and credits

Everything Andy uses that isn't ours, with its terms and the credit it asks for.

This repository is Apache-2.0 ([LICENSE](../LICENSE)). It uses, under their own terms:

| What | Licence or terms | Credit |
|---|---|---|
| NVIDIA Parakeet TDT 0.6B v3 (hearing) | CC-BY-4.0 | NVIDIA, [model card](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) |
| NVIDIA Nemotron 3.5 Lightning and Nemotron 3 Ultra | Used through Nebius Token Factory under its terms; NVIDIA's model licences | NVIDIA, Nebius |
| NVIDIA Nemotron 3.5 Super VL (eyes, since 2026-10-20) | Used through Nebius Token Factory under its terms; NVIDIA's model licence | NVIDIA, Nebius |
| NVIDIA Nemotron Nano 12B v2 VL FP8 (eyes on our own endpoint, the option) | NVIDIA's open model licence ([model card](https://huggingface.co/nvidia/NVIDIA-Nemotron-Nano-12B-v2-VL-FP8)) | NVIDIA |
| NVIDIA Cosmos Reason 2 2B and 8B (the offline eyes, served by vLLM on this computer, `local-eyes/`) | NVIDIA Open Model License ([2B](https://huggingface.co/nvidia/Cosmos-Reason2-2B), [8B](https://huggingface.co/nvidia/Cosmos-Reason2-8B) model cards) | NVIDIA |
| NVIDIA Nemotron 3.5 Content Safety (second look) | OpenMDW-1.1, Gemma Terms of Use and Prohibited Use Policy | NVIDIA, Google (Gemma) |
| Qwen3-TTS (speaking); the recorded urgent sentences in `src/andy_companion/urgent_audio/` were made with Qwen3-TTS-12Hz-1.7B-CustomVoice, voice "Aiden" (`regenerate.py` there) | Apache-2.0 | Qwen team, Alibaba |
| Silero VAD and Smart Turn v3.2 (when the person has finished speaking), through speech-to-speech | MIT (Silero VAD); BSD-2-Clause (Smart Turn) | Silero team; Pipecat (Daily) |
| NVIDIA Magpie TTS Multilingual 357M and NVIDIA NeMo (evaluated in `voice/magpie-eval/`, not used by Andy) | NVIDIA Open Model License (the model); Apache-2.0 (NeMo) | NVIDIA |
| Pollen Robotics' Reachy Mini SDK and conversation app (`reachy_app/andy_companion_app/main.py` mirrors about 15 lines of the app's `ReachyMiniConversationApp.run`) | Apache-2.0 | Pollen Robotics |
| Pollen's MuJoCo scene for the Reachy Mini (`sim/`: fetched from the `reachy_mini` package on PyPI at run time; the scene itself is not stored in this repository, only our renders of it, `docs/images/sim-search.gif` and `.mp4`) | Apache-2.0, with the package | Pollen Robotics |
| MuJoCo (the simulation) | Apache-2.0 | Google DeepMind |
| OpenCV (camera pictures, the wave) and Tesseract (reading letters) | Apache-2.0 each | OpenCV team; Tesseract contributors |
| YOLOX person detection from the OpenCV model zoo (`object_detection_yolox_2022nov.onnx`, fetched from Hugging Face at a pinned revision, `body/person.py`) | Apache-2.0 | Megvii (YOLOX); OpenCV model zoo |
| vLLM (serving models on our own Nebius endpoints) | Apache-2.0 | vLLM project |
| Hugging Face speech-to-speech | Apache-2.0 | Hugging Face |
| Vosk and its small English and Spanish models, `vosk-model-small-en-us-0.15` and `vosk-model-small-es-0.42` (wake phrase) | Apache-2.0 (each model as listed by Alpha Cephei) | Alpha Cephei |
| segno (the settings QR code) | BSD-3-Clause | Lars Heuer |
| Tavily API (the web) | Tavily's terms of service | Tavily |
| National Weather Service API (the weather) | US government work, public domain | NOAA / NWS |
| Open-Meteo geocoding (the town's coordinates, once) | Free non-commercial use; data CC-BY-4.0 (GeoNames) | Open-Meteo, GeoNames |
| Atkinson Hyperlegible (the screens' typeface), bundled in `src/andy_companion/pages/fonts/` and served by Andy itself | SIL Open Font License (`fonts/OFL.txt`) | Braille Institute |
| Wikipedia's On this day (fetched at runtime, never stored in this repository) | CC BY-SA 4.0 | "According to Wikipedia" said aloud; "Wikipedia (CC BY-SA 4.0)" on the screen |
| The stories (`src/andy_companion/story_texts.json`): *The Aesop for Children* (1919), O. Henry's *The Four Million* (1906), Kipling's *Just So Stories* (1902) | Public domain in the United States; texts from Project Gutenberg with its header and licence removed, as its licence allows | The authors, named on screen as each story is read |
| Sample landscapes (`scripts/settings.py sample-photos`, downloaded only on request, never in this repository) | Unsplash License, via Lorem Picsum | Each photographer, credited on screen |
