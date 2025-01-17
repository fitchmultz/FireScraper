# FireScraper Tools

A collection of web scraping and content extraction tools using the FireCrawl API.

## Scripts Overview

### 1. `claude_firecrawl.py` - Intelligent Search & Content Extraction

- **Purpose**: Targeted search and intelligent content extraction based on specific objectives
- **Key Features**:
  - Uses Claude AI for search optimization and content analysis
  - Combines site mapping and targeted scraping
  - Extracts specific information based on user objectives
- **API Usage**: `map` and `scrape` endpoints
- **Best For**: Finding specific information across a website

### 2. `claude_scrape_page.py` - Detailed Single Page Analysis

- **Purpose**: Deep content extraction and structuring from individual pages
- **Key Features**:
  - Structured JSON output with metadata
  - Intelligent content organization
  - Markdown formatting preservation
- **API Usage**: `scrape` endpoint
- **Best For**: Detailed analysis and structuring of single web pages

### 3. `crawl.py` - Full Website Archival

- **Purpose**: Bulk website crawling and content archiving
- **Key Features**:
  - English language filtering
  - URL deduplication
  - Progress tracking
  - File system organization
- **API Usage**: `crawl` endpoint
- **Best For**: Archiving entire websites or sections

## Key Differences

| Feature        | claude_firecrawl.py  | claude_scrape_page.py | crawl.py       |
| -------------- | -------------------- | --------------------- | -------------- |
| API Endpoints  | map + scrape         | scrape only           | crawl          |
| AI Integration | Search & Analysis    | Content Structuring   | None           |
| Scope          | Targeted Search      | Single Page           | Full Site      |
| Output         | Specific Information | Structured JSON       | Markdown Files |
| Storage        | Memory               | Memory                | File System    |

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:

   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Required API keys:

   - `FIRECRAWL_API_KEY` - For FireCrawl API access
   - `ANTHROPIC_API_KEY` - For Claude AI integration (not needed for crawl.py)

## Usage Examples

### Intelligent Search

```python
python claude_firecrawl.py
# Enter website and search objective when prompted
```

### Single Page Analysis

```python
python claude_scrape_page.py
# Enter URL when prompted
```

### Full Site Crawl

```python
python crawl.py <url>
```

## Output Formats

1. **claude_firecrawl.py**:

   ```json
   {
     "relevant_info": "Extracted information matching objective",
     "source_url": "URL where information was found"
   }
   ```

2. **claude_scrape_page.py**:

   ```json
   {
     "title": "Page title",
     "description": "Brief description",
     "content": "Main content in markdown",
     "metadata": {
       "last_updated": "Update date",
       "author": "Author name",
       "reading_time": "Estimated minutes"
     }
   }
   ```

3. **crawl.py**:

- Creates a directory structure:

  ```txt
  crawls/
  └── domain.com/
      ├── page1.md
      ├── page2.md
      └── visited_urls.txt
  ```

## Error Handling

All scripts include:

- Graceful error handling
- Progress indicators
- Color-coded console output
- Timeout protection

## Rate Limiting

Please be mindful of the FireCrawl API rate limits:

- Respect the API's concurrent request limits
- Use appropriate delays between requests
- Monitor credit usage through the API dashboard
