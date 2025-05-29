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

# Check if deekseek model is installed
if ! curl -s http://localhost:11434/api/tags | grep -q "deepseek-r1:7b"; then
    echo "⚠️  DeepSeek not found"
    ollama pull deepseek-r1:7b

fi

echo "🚀 Starting SCS Excel Processor..."
docker-compose up --build