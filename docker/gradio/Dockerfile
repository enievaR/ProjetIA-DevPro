FROM python:3.12-slim


COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Installe les deps Python en premier pour bénéficier du cache Docker
COPY pyproject.toml README.md ./
COPY src /app/src
RUN uv pip install --system --no-cache-dir -e .

# User non-root
RUN useradd --uid 1000 --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 7860

CMD ["python", "-m", "src.gradio_app.main"]