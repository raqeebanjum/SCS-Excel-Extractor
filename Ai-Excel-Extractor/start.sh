#!/bin/bash

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama is not running. Please start Ollama first."
    exit 1
fi

# Check if mistral model is installed
if ! curl -s http://localhost:11434/api/tags | grep -q "mistral"; then
    echo "⚠️  Mistral model not found. Installing..."
    ollama pull mistral
fi

echo "🚀 Starting Industrial Data Processor..."
docker-compose up --build