# Andy beside NVIDIA's Reachy Mini Jetson assistant

NVIDIA's [Reachy Mini Jetson Assistant](https://www.jetson-ai-lab.com/tutorials/reachy-mini-jetson-assistant)
(Jetson AI Lab, read 2026-10-20) runs everything on the robot's own small computer. Andy makes different choices;
the README says why. Side by side:

| | The Jetson assistant | Andy |
|---|---|---|
| Computer | Jetson Orin Nano 8 GB, about 7.6 GB usable | A desktop with an NVIDIA GPU beside the robot; hearing and speaking use about 7.1 GB |
| Starting a turn | Push-to-talk in a web page; Silero VAD | A spoken wake phrase, offline (Vosk), English and Spanish; then natural turn-taking, and you can talk over Andy |
| Hearing | faster-whisper | NVIDIA Parakeet TDT 0.6B v3, on this computer |
| Thinking and seeing | Cosmos Reason 2 2B, 4-bit (about 2.2 GB), llama.cpp, on the Jetson | Nemotron 3.5 Lightning, Nemotron 3 Ultra and Nemotron 3.5 Super VL on Nebius Token Factory, zero data retention |
| Speaking | Kokoro | Qwen3-TTS, on this computer |
| Moving | One 100 Hz controller, so face tracking and speaking gestures never fight | The same idea in Pollen's movement manager: one loop at 60 Hz is the only thing that sets the motors; following your face is blended in, and glances at the TV, the finder's sweep and the antennas wait in its one queue |
| A picture for the model | Motion frozen briefly before the frame is chosen | The head stops and settles 0.6 s before each frame |
| Published speed | None given | Median 1.06 s from your words being understood to Andy's first sound, 54 real turns ([scorecard](../evals/results/robot-timings-2026-10-20-1550.json)) |
