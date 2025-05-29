@echo off
setlocal

echo 🛠️ Building Docker image...
docker build --no-cache -t excel-matcher .

echo 🚀 Running container...
docker run --rm -v "%cd%":/app excel-matcher

endlocal
pause