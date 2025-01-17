# FireCrawl API Reference (v1)

## Authentication

All endpoints require an API key passed in the `Authorization` header:

```txt
Authorization: Bearer YOUR_API_KEY
```

## Common Headers

### Idempotency

For POST requests that modify state, you can include an idempotency key:

```txt
X-Idempotency-Key: <unique-key>
```

## Core Endpoints

### Scraping

#### `POST /v1/scrape`

Single page scraping with JavaScript rendering.

**Request Body:**

```json
{
  "url": "https://example.com",
  "formats": ["markdown"] // Optional: defaults to markdown
}
```

**Response:**

```json
{
  "markdown": "...",
  "metadata": {
    "url": "...",
    "title": "..."
    // Additional metadata
  }
}
```

#### `GET /v1/scrape/:jobId`

Get status and results of a scrape job.

#### `POST /v1/batch/scrape`

Scrape multiple URLs in parallel.

**Request Body:**

```json
{
  "urls": ["https://example1.com", "https://example2.com"],
  "formats": ["markdown"]
}
```

#### `GET /v1/batch/scrape/:jobId`

Get status and results of a batch scrape job.

### Crawling

#### `POST /v1/crawl`

Start a website crawl.

**Request Body:**

```json
{
  "url": "https://example.com",
  "allowExternalLinks": false,
  "allowSubdomains": true,
  "maxDepth": 10
}
```

**Response:**

```json
{
  "id": "job_id",
  "status": "pending"
}
```

#### `GET /v1/crawl/:jobId`

Get crawl job status and results.

#### `DELETE /v1/crawl/:jobId`

Cancel an active crawl job.

#### `WS /v1/crawl/:jobId`

WebSocket connection for real-time crawl updates.

### Site Mapping

#### `POST /v1/map`

Generate a map of URLs from a website.

**Request Body:**

```json
{
  "url": "https://example.com",
  "search": "optional search term",
  "limit": 5000,
  "ignoreSitemap": false,
  "includeSubdomains": true
}
```

**Response:**

```json
{
  "links": ["..."],
  "job_id": "...",
  "time_taken": 1.23
}
```

### Content Extraction

#### `POST /v1/extract`

Extract specific content from URLs.

**Request Body:**

```json
{
  "url": "https://example.com",
  "selectors": {
    "title": "h1",
    "content": "article"
  }
}
```

#### `GET /v1/extract/:jobId`

Get extraction job status and results.

### Search

#### `POST /v1/search`

Search through crawled content.

**Request Body:**

```json
{
  "query": "search terms",
  "limit": 10
}
```

### Account Management

#### `GET /v1/team/credit-usage`

Get team credit usage statistics.

**Response:**

```json
{
  "credits_used": 100,
  "credits_remaining": 900,
  "usage_period": "2024-01"
}
```

### Status Monitoring

#### `GET /v1/concurrency-check`

Check concurrent job limits and availability.

## Rate Limiting

Each endpoint has specific rate limiting modes:

- Scrape mode for scraping endpoints
- Crawl mode for crawling endpoints
- Map mode for mapping endpoints
- Search mode for search endpoints
- Extract mode for extraction endpoints
- CrawlStatus mode for status endpoints

Rate limit information is returned in response headers:

- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

## Credit System

Each request requires a minimum number of credits:

- Single page operations: 1 credit
- Batch operations: 1 credit per URL
- Search operations: Based on limit parameter
- Map operations: 1 credit minimum

Insufficient credits will result in a 402 Payment Required response.

## URL Restrictions

Some URLs may be blocked for various reasons (e.g., security, terms of service).
Attempting to access blocked URLs will result in a 403 Forbidden response.

## Error Responses

All error responses follow this format:

```json
{
  "success": false,
  "error": "Error message description"
}
```

Common HTTP status codes:

- `400` - Bad Request
- `401` - Unauthorized
- `402` - Payment Required (insufficient credits)
- `403` - Forbidden (including blocked URLs)
- `409` - Conflict (duplicate idempotency key)
- `429` - Too Many Requests
- `500` - Internal Server Error

## Best Practices

1. **Concurrency Management**

   - Use the concurrency check endpoint
   - Implement exponential backoff for retries

2. **Resource Usage**

   - Monitor credit usage
   - Use batch endpoints for multiple URLs
   - Implement proper error handling

3. **Performance**

   - Use WebSocket connections for long-running jobs
   - Implement proper timeout handling
   - Cache results when appropriate

4. **Idempotency**
   - Use idempotency keys for state-changing operations
   - Store and reuse idempotency keys for retries
