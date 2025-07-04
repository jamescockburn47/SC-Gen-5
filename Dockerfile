FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    ghostscript \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY pyproject.toml .
COPY README.md .

# Install the package
RUN pip install -e .

# Create data directory
RUN mkdir -p /app/data/vector_db

# Expose ports
EXPOSE 8000 8001 8501

# Default command (can be overridden)
CMD ["python", "-m", "uvicorn", "sc_gen5.services.consult_service:app", "--host", "0.0.0.0", "--port", "8000"] 