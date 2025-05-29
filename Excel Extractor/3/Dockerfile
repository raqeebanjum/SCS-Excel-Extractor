FROM python:3.10-slim

WORKDIR /app

# Copy source code and inputs
COPY src/ /app/src/
COPY input/ /app/input/

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir pandas openpyxl fuzzywuzzy python-Levenshtein

# Set entrypoint
CMD ["python", "src/main.py"]