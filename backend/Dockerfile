# ── Backend: FastAPI + SQLAlchemy + Scoring Engine ──
FROM python:3.11-slim

WORKDIR /app

# System deps for cryptography (PyJWT RS256)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from pyproject.toml
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    fastapi uvicorn[standard] sqlalchemy aiosqlite \
    alembic pydantic-settings pyyaml jinja2 arq \
    requests python-dotenv anthropic openai pyjwt \
    stripe cryptography

# Copy all source code
COPY . .

# SQLite DB will live here (volume-mount in production)
RUN mkdir -p /app/data
ENV DATABASE_URL=sqlite+aiosqlite:///./data/brand_compass.db
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
