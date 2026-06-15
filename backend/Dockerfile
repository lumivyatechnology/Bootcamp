FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY Makefile .
COPY pyproject.toml .
COPY samsung_phones_specs.csv .

RUN uv sync --no-cache --group etl

ADD src /app/src

CMD ["uv", "run", "/app/src/main.py"]

