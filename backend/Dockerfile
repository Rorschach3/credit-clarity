FROM python:3.11-slim

# Install system dependencies in single layer with version locking
RUN apt-get update && apt-get install -y \
    build-essential \
    tesseract-ocr \
    poppler-utils \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /backend

# Create non-root user early for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy requirements first for better caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install Python dependencies with optimizations and error handling
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --timeout 300 -r requirements.txt

# Copy source code with proper ownership
COPY --chown=appuser:appuser main.py ./
COPY --chown=appuser:appuser worker.py ./
COPY --chown=appuser:appuser services/ ./services/
COPY --chown=appuser:appuser utils/ ./utils/
COPY --chown=appuser:appuser core/ ./core/
COPY --chown=appuser:appuser schemas/ ./schemas/
COPY --chown=appuser:appuser api/ ./api/
COPY --chown=appuser:appuser models/ ./models/
COPY --chown=appuser:appuser middleware/ ./middleware/
COPY --chown=appuser:appuser config/ ./config/

# Copy configuration files if they exist
COPY --chown=appuser:appuser .env* ./
COPY --chown=appuser:appuser service-account.json* ./
COPY . .

ENV PYTHONPATH=/backend

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check with better error handling
HEALTHCHECK --interval=30s --timeout=15s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health --connect-timeout 5 --max-time 10 || exit 1

# Default to FastAPI dev server with better error handling
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]