---
title: Andy, on sample data
emoji: 🤖
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
license: apache-2.0
short_description: A home robot's screens, for older adults and family
---

# Andy's screens, on sample data

Andy is a small home robot for older adults who live at home, and the family who help. It runs on a
Pollen Robotics Reachy Mini and is built with NVIDIA Nemotron on Nebius Token Factory, and Tavily.

This Space runs Andy's real screen server on made-up data, with no robot, model or keys: the TV beside
Andy, Under the hood, the family page and the settings page. It is read-only: nothing a visitor types is
kept or shown to anyone.

Its front page also plays a 20-second film of Andy's own search, in Pollen's MuJoCo simulation, with live calls to
NVIDIA Nemotron 3.5 Super VL. The code, the measurements and how to run everything:
https://github.com/AndyDM9/andy-companion
