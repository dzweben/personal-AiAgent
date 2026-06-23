# a slim image to run the agent or the api without fussing with a local python.
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# install deps first so docker can cache this layer
COPY pyproject.toml requirements.txt ./
RUN pip install --upgrade pip && pip install ".[server,rag]" || pip install -r requirements.txt

# now the actual code
COPY . .
RUN pip install -e . || true

# default to the cli. override the command to run the api instead:
#   docker run -p 8000:8000 personal-aiagent python -m agent.server
EXPOSE 8000
ENTRYPOINT ["python"]
CMD ["main.py"]
