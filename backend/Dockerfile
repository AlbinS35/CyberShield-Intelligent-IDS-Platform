FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn uvicorn[standard] whitenoise

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# Start with gunicorn for production
CMD ["gunicorn", "cybershield_core.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
