# Build and run with Docker Compose
docker-compose up --build

# Or to run in detached mode
docker-compose up -d --build

##
docker-compose up ollama
docker-compose run extractor python Extractor.py


docker-compose run extractor
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser