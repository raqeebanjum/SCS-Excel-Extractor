# Use Python base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make sure the input.xlsx file is in the container
COPY input.xlsx .

# Expose port for Ollama
EXPOSE 11434

# Create a script to run both Ollama and the Python script
COPY start.sh .
RUN chmod +x start.sh

# Set the entry point
ENTRYPOINT ["./start.sh"]