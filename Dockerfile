# Use Python 3.12 slim image for a smaller footprint
FROM python:3.12-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies required for building Python packages (e.g. psycopg2)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /app/.venv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# --- Runtime Stage ---
FROM python:3.12-slim

WORKDIR /app

# Install runtime system dependencies (libpq for postgres)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Set environment variables to use the venv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy source code
COPY src ./src

# Add src to PYTHONPATH so react_agent can be imported
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=7999

# Expose the port
EXPOSE 7999 

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:7999/health || exit 1

# Command to run the application
CMD ["uvicorn", "react_agent.server:app", "--host", "0.0.0.0", "--port", "7999"]


