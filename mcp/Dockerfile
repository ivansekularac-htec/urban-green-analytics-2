FROM python:3.12-slim

WORKDIR /app

ENV MCP_PORT=8001

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE ${MCP_PORT}

CMD ["python", "-m", "app.main"]
