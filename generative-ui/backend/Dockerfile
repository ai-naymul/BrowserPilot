FROM python:3.12-slim

WORKDIR /app

# System deps: gcc for any source builds; libxml2/libxslt for lxml + trafilatura.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* ./
# --no-root: this is an app, not an installable package; --only main: skip dev deps.
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main

COPY . .

EXPOSE 8001

# Correct entrypoint is app.main:app (the old `main:app` did not exist).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
