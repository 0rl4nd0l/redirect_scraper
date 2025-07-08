# Make.com HTTP Module Integration Guide

This guide shows how to integrate your redirect scraper with Make.com's HTTP module for automated workflows.

## Prerequisites

1. **Deploy your redirect scraper** to a public URL (Railway, Heroku, etc.)
2. **Make.com account** with HTTP module access
3. **API endpoint** accessible from the internet

## Make.com HTTP Module Configurations

### 1. **Single URL Scraping (GET Request)**

**Module**: HTTP > Make a Request

**Configuration**:
```
URL: https://worker-production-47c2.up.railway.app/scrape
Method: GET
Query String:
  - url: {{trigger.url}}
  - user_agent: Make.com-Bot/1.0

Headers:
  - Content-Type: application/json
  - Accept: application/json
```

**Sample URL**: `https://your-app.railway.app/scrape?url=https://example.com&user_agent=Make.com-Bot/1.0`

### 2. **Advanced URL Fetching (POST Request)**

**Module**: HTTP > Make a Request

**Configuration**:
```
URL: https://your-app.railway.app/fetch/
Method: POST
Body Type: Raw
Content Type: application/json

Body:
{
  "url": "{{trigger.url}}",
  "user_agent": "Make.com-Bot/1.0",
  "timeout": 15
}

Headers:
  - Content-Type: application/json
  - Accept: application/json
```

### 3. **Batch URL Processing**

**Module**: HTTP > Make a Request

**Configuration**:
```
URL: https://your-app.railway.app/batch-fetch/
Method: POST
Body Type: Raw
Content Type: application/json

Body:
[
  "{{trigger.url1}}",
  "{{trigger.url2}}",
  "{{trigger.url3}}"
]

Headers:
  - Content-Type: application/json
  - Accept: application/json
```

## Make.com Scenario Examples

### Scenario 1: **URL Monitoring Workflow**

1. **Trigger**: Webhook or Schedule
2. **HTTP Module**: Call `/scrape` endpoint
3. **Filter**: Check if `status_code` = 200
4. **Action**: Send email/Slack notification if URL is down

**HTTP Module Setup**:
```json
{
  "url": "https://your-app.railway.app/scrape",
  "method": "GET",
  "qs": {
    "url": "{{1.url}}",
    "user_agent": "Make.com-Monitor/1.0"
  }
}
```

### Scenario 2: **Content Change Detection**

1. **Trigger**: Schedule (every hour)
2. **HTTP Module**: Call `/fetch/` endpoint
3. **Data Store**: Compare with previous content
4. **Action**: Notify if content changed

**HTTP Module Setup**:
```json
{
  "url": "https://your-app.railway.app/fetch/",
  "method": "POST",
  "body": {
    "url": "{{trigger.website_url}}",
    "user_agent": "Make.com-ContentMonitor/1.0",
    "timeout": 20
  },
  "headers": {
    "Content-Type": "application/json"
  }
}
```

### Scenario 3: **Bulk URL Processing**

1. **Trigger**: Google Sheets (new row)
2. **HTTP Module**: Call `/batch-fetch/` with URLs from sheet
3. **Iterator**: Process each result
4. **Action**: Update sheet with results

**HTTP Module Setup**:
```json
{
  "url": "https://your-app.railway.app/batch-fetch/",
  "method": "POST",
  "body": [
    "{{1.url1}}",
    "{{1.url2}}",
    "{{1.url3}}"
  ],
  "headers": {
    "Content-Type": "application/json"
  }
}
```

## Response Handling in Make.com

### Expected Response Structure
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

### Accessing Response Data in Make.com

- **Final URL**: `{{http.final_url}}`
- **Status Code**: `{{http.status_code}}`
- **Content Type**: `{{http.content_type}}`
- **Redirect Count**: `{{http.redirect_count}}`
- **Response Time**: `{{http.response_time}}`
- **Content Preview**: `{{http.content_preview}}`

## Error Handling

### Common Error Responses
```json
{
  "detail": "Request failed: Connection timeout"
}
```

### Make.com Error Handling
1. **Add Error Handler**: Right-click HTTP module → Add error handler
2. **Filter Errors**: Check `{{http.status_code}}` >= 400
3. **Handle Gracefully**: Log error or retry with different parameters

## Authentication (Optional)

If you add authentication to your API:

```json
{
  "headers": {
    "Authorization": "Bearer {{connection.api_key}}",
    "Content-Type": "application/json"
  }
}
```

## Rate Limiting Considerations

- **Concurrent Requests**: Your API handles concurrent requests well
- **Timeout Settings**: Set appropriate timeouts in Make.com (30-60 seconds)
- **Retry Logic**: Use Make.com's built-in retry mechanisms

## Testing Your Integration

1. **Test Single Request**: Use `/scrape` endpoint with a known URL
2. **Test Error Handling**: Use invalid URL to test error responses
3. **Test Batch Processing**: Send multiple URLs to `/batch-fetch/`
4. **Monitor Performance**: Check response times and success rates

## Deployment Checklist

- [ ] Deploy API to public URL (Railway/Heroku)
- [ ] Test all endpoints are accessible
- [ ] Configure proper CORS if needed
- [ ] Set up monitoring/logging
- [ ] Test with Make.com HTTP module
- [ ] Set up error handling in Make.com
- [ ] Document API endpoints for team

## Sample Make.com Scenario JSON

```json
{
  "scenario": {
    "name": "URL Redirect Scraper",
    "modules": [
      {
        "id": 1,
        "module": "webhook",
        "name": "Webhook Trigger"
      },
      {
        "id": 2,
        "module": "http",
        "name": "Scrape URL",
        "parameters": {
          "url": "https://your-app.railway.app/fetch/",
          "method": "POST",
          "body": {
            "url": "{{1.url}}",
            "user_agent": "Make.com-Scraper/1.0"
          }
        }
      },
      {
        "id": 3,
        "module": "email",
        "name": "Send Results",
        "parameters": {
          "subject": "Scrape Results",
          "body": "Final URL: {{2.final_url}}\nStatus: {{2.status_code}}\nRedirects: {{2.redirect_count}}"
        }
      }
    ]
  }
}
```

## Pro Tips

1. **Use Webhooks**: For real-time processing
2. **Batch Processing**: More efficient for multiple URLs
3. **Error Handling**: Always add error handlers in Make.com
4. **Data Stores**: Use for comparing content over time
5. **Filters**: Add filters to handle different response types
6. **Monitoring**: Set up alerts for failed requests

## Support

- **API Documentation**: Available at `https://your-app.railway.app/docs`
- **Health Check**: `https://your-app.railway.app/health`
- **Test Endpoint**: Use `/scrape?url=https://httpbin.org/get` for testing

