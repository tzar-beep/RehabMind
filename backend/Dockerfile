# RehabMind backend image: API (uvicorn) and worker (ARQ + faster-whisper) share it.
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

RUN pip install --no-cache-dir uv==0.11.21

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app

# Unprivileged runtime user; model cache lives in a volume under its home.
RUN useradd --system --uid 10001 --create-home app \
    && mkdir -p /home/app/.cache \
    && chown -R app:app /home/app
USER app
ENV PATH=/opt/venv/bin:$PATH \
    HF_HOME=/home/app/.cache/huggingface

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=12 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health/live')" || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header", "--proxy-headers"]
