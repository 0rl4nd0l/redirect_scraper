#!/bin/bash

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium --with-deps

# Start the FastAPI application
echo "Starting FastAPI application..."
uvicorn app:app --host=0.0.0.0 --port=$PORT
