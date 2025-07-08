# Redirect Scraper with Enhanced HTTP Integration

A FastAPI-based web scraper with comprehensive HTTP integration features including async client support, session management, retry logic, and batch processing.

## Features

### 🚀 **HTTP Integration Enhancements**

- **Async HTTP Client**: Uses `httpx` for non-blocking HTTP requests
- **Session Management**: Connection pooling and reuse with `requests.Session()`
- **Retry Logic**: Automatic retries on network failures with exponential backoff
- **Middleware**: Request/response logging and performance metrics
- **Batch Processing**: Concurrent fetching of multiple URLs
- **Enhanced Error Handling**: Comprehensive error responses and logging

### 🔧 **Configuration Options**

- Custom User-Agent strings
- Authorization token support
- Configurable timeouts
- Connection pooling settings
- Retry strategies

## API Endpoints

### 1. **Health Check**
```http
GET /health
```
Returns service health status.

### 2. **Synchronous Scrape**
```http
GET /scrape?url=https://example.com&user_agent=Custom-Agent
```
Scrapes a single URL using enhanced session management.

### 3. **Asynchronous Fetch**
```http
POST /fetch/
Content-Type: application/json

{
    "url": "https://example.com",
    "user_agent": "Custom-Agent/1.0",
    "auth_token": "Bearer token",
    "timeout": 15
}
```
Asynchronously fetches URL content with enhanced error handling.

### 4. **Batch Fetch**
```http
POST /batch-fetch/
Content-Type: application/json

[
    "https://example1.com",
    "https://example2.com",
    "https://example3.com"
]
```
Fetches multiple URLs concurrently.

## Response Format

All endpoints return a structured response:

```json
{
    "final_url": "https://example.com",
    "status_code": 200,
    "content_type": "text/html; charset=utf-8",
    "content_length": 1234,
    "redirect_count": 2,
    "response_time": 0.543,
    "headers": {
        "Content-Type": "text/html; charset=utf-8",
        "Server": "nginx/1.20.1"
    },
    "content_preview": "<!DOCTYPE html>..."
}
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
uvicorn app:app --reload --port 8000
```

## Testing

Run the test script to verify all HTTP integration features:

```bash
python test_http_integration.py
```

Or use the interactive API documentation at `http://127.0.0.1:8000/docs`

## HTTP Features in Detail

### Session Management
- **Connection Pooling**: Reuses connections for better performance
- **Retry Strategy**: Automatic retries on 429, 500, 502, 503, 504 status codes
- **Timeout Configuration**: Per-request timeout settings
- **Header Management**: Enhanced header configuration with authentication support

### Middleware
- **Request Logging**: Logs all incoming requests with timestamps
- **Performance Metrics**: Adds `X-Process-Time` header to responses
- **Response Headers**: Adds custom server identification headers

### Error Handling
- **Comprehensive Exception Handling**: Catches and categorizes different error types
- **Structured Error Responses**: Returns detailed error information
- **Logging**: Detailed error logging for debugging

### Async Support
- **Non-blocking Operations**: Uses `httpx.AsyncClient` for concurrent requests
- **Batch Processing**: Handles multiple URLs simultaneously
- **Resource Management**: Proper cleanup of async resources

## Configuration

The HTTP integration can be configured through environment variables or by modifying the configuration functions:

- `create_http_session()`: Configure retry strategy and connection pooling
- `get_headers()`: Customize default headers and authentication
- Middleware settings for logging and metrics

## Dependencies

- `fastapi`: Web framework
- `httpx`: Async HTTP client
- `requests`: Synchronous HTTP client
- `urllib3`: HTTP library with retry logic
- `pydantic`: Data validation
- `uvicorn`: ASGI server

## License

MIT License

