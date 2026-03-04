FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Copy all source files first (needed for editable install)
COPY . .

# Install dependencies (editable mode for development)
RUN pip install --no-cache-dir -e ".[dev]"

# Default command: run the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
