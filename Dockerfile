# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY templates/ ./templates/
COPY static/ ./static/
COPY create_admin.py ./

# Install dependencies
RUN uv sync --frozen

# Create directory for SQLite database
RUN mkdir -p /app/data

# Set environment variables for production
ENV DATABASE_URL=sqlite:///./data/deadman_switch.db
ENV SECRET_KEY=your-production-secret-key-change-this-in-production
ENV HOST=0.0.0.0
ENV PORT=8000

# Expose port
EXPOSE 8000

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Running database migrations..."\n\
uv run alembic upgrade head\n\
echo "Creating admin user..."\n\
uv run python create_admin.py\n\
echo "Starting application..."\n\
exec uv run gunicorn deadman_switch.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT\n\
' > /app/start.sh && chmod +x /app/start.sh

# Run the application
CMD ["/app/start.sh"]
