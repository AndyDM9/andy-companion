# Andy's screens on sample data, for anyone to open: a Hugging Face Space (PLAN B26).
# Built by scripts/space.sh, which copies only what the demo needs beside this file. No keys, no robot, no
# model: scripts/demo_screen.py --public serves the four pages read-only.
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends tzdata && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.12.20 /uv /bin/uv
RUN useradd -m -u 1000 user
USER user
RUN mkdir -p /home/user/app        # made by the user, so uv can write its environment here
WORKDIR /home/user/app
ENV TZ=America/New_York PYTHONUNBUFFERED=1 UV_NO_CACHE=1 UV_PYTHON_DOWNLOADS=never
COPY --chown=user pyproject.toml uv.lock LICENSE ./
# The demo needs only numpy, OpenCV (headless) and segno, all in the locked dev group; Andy itself isn't installed.
RUN uv sync --frozen --no-install-project
COPY --chown=user src ./src
COPY --chown=user scripts/demo_screen.py ./scripts/demo_screen.py
COPY --chown=user sim-search.mp4 ./sim-search.mp4
ENV ANDY_DEMO_PUBLIC=1 PORT=7860
EXPOSE 7860
CMD ["uv", "run", "--frozen", "--no-sync", "python", "scripts/demo_screen.py", "--public"]
