FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src /app/src
RUN uv pip install --system --no-cache-dir -e .

COPY workflows /app/workflows

RUN useradd --uid 1000 --create-home --shell /bin/bash app \
    && mkdir -p /data/images \
    && chown -R app:app /app /data/images
USER app

CMD ["python", "-m", "src.worker.main"]