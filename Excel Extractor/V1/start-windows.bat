@echo off
echo Checking requirements...

REM Check if Docker is running
docker info > nul 2>&1
if errorlevel 1 (
    echo [31m❌ Docker is not running. Please start Docker Desktop first.[0m
    pause
    exit /b 1
)

REM Check if Ollama is running
curl -s http://localhost:11434/api/tags > nul
if errorlevel 1 (
    echo [31m❌ Ollama is not running. Please start Ollama first.[0m
    pause
    exit /b 1
)

REM Check if mistral model is installed
curl -s http://localhost:11434/api/tags | findstr "mistral" > nul
if errorlevel 1 (
    echo [33m⚠️  Mistral model not found. Installing...[0m
    ollama pull mistral
)

echo [32m🚀 Starting SCS Excel Processor...[0m
docker-compose up --build
pause