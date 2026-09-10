FROM python:3.11-slim

WORKDIR /app

# Build context is the repo root (see docker-compose.yml) because server/main.py
# imports research_assistant.graph - both packages are needed for `pip install -e .`.
COPY pyproject.toml ./
COPY research_assistant ./research_assistant
COPY server ./server

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
