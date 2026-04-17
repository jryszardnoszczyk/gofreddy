FROM python:3.13-slim

# Build essentials for asyncpg + cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY cli ./cli
COPY portal ./portal
COPY scripts ./scripts

# Install only the deps needed to serve the API. The CLI tree is copied for
# completeness (future freddy sync endpoint may import from it) but the image
# runs only uvicorn.
RUN pip install --no-cache-dir -e .

# Mount point for client data (Fly volume)
RUN mkdir -p /data/clients

ENV PYTHONUNBUFFERED=1 \
    PORT=8080 \
    GOFREDDY_CLIENTS_DIR=/data/clients

EXPOSE 8080

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
