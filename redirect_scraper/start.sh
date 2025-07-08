#!/bin/bash

# Start the FastAPI application immediately
echo "Starting FastAPI application..."
uvicorn app:app --host=0.0.0.0 --port=$PORT
