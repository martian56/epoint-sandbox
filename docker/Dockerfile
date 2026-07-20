FROM oven/bun:1.3-alpine AS web
WORKDIR /build
COPY package.json bun.lock* ./
COPY apps/web/package.json apps/web/
RUN bun install --frozen-lockfile || bun install
COPY apps/web apps/web
COPY biome.json ./
RUN cd apps/web && bun run build


FROM python:3.12-slim AS deps

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY apps/api/pyproject.toml apps/api/uv.lock* ./
RUN uv sync --no-dev --no-install-project

COPY apps/api/src ./src
RUN uv sync --no-dev


FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PGDATA=/var/lib/postgresql/data \
    EPOINT_PORT=8181 \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
      postgresql curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Only the virtualenv comes across, so uv itself never ships.
COPY --from=deps /app/.venv ./.venv

COPY apps/api/src ./src
COPY apps/api/migrations ./migrations
COPY apps/api/alembic.ini ./
COPY --from=web /build/apps/web/dist ./src/epoint_sandbox/static

COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
# Strip CR so a checkout made on Windows still finds its interpreter.
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh \
    && chmod +x /usr/local/bin/entrypoint.sh \
    && mkdir -p /var/lib/postgresql/data \
    && chown -R postgres:postgres /var/lib/postgresql

EXPOSE 8181

HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=5 \
  CMD curl -fsS http://localhost:8181/api/heartbeat || exit 1

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
