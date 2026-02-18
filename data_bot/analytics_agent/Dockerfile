FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY Makefile .
COPY pyproject.toml .

RUN uv sync --no-cache

ADD src /app/src

CMD ["uv", "run", "/app/src/main.py"]

