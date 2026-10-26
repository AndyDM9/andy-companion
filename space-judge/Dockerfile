FROM python:3.12-slim
RUN useradd -m -u 1000 andy
WORKDIR /app
COPY --chown=1000:1000 . /app
USER 1000
ENV PORT=7860 PYTHONUNBUFFERED=1
EXPOSE 7860
CMD ["python", "scripts/judge_playground.py"]
