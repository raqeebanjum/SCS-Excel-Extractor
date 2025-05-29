#!/bin/bash

set -e 

echo "Building image..."
docker build --no-cache -t excel-matcher .

echo "Running container..."
docker run --rm -v "$PWD":/app excel-matcher