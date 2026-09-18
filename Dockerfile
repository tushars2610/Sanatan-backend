FROM python:3.12-slim

# System dependencies for compiling C-extensions (pyswisseph) and runtime utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and configurations
COPY app ./app
COPY panchang.py places.py load_to_postgress.py index_to_milvus.py ./
COPY migrations ./migrations
COPY alembic.ini* .env.example ./

EXPOSE 8000

# Default command starts FastAPI with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
