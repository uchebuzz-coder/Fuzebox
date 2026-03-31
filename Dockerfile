FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies for matplotlib and numpy
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Health check for Streamlit
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health').read()" || exit 1
EXPOSE 8501

CMD ["streamlit", "run", "dashboard_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
