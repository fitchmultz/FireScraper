# FireScraper Tools

A collection of web scraping and content extraction tools using the FireCrawl API.

## Project Structure

```bash
FireScraper/
├── api/                     # API server
│   ├── src/                # Source code
│   │   ├── controllers/    # Request handlers
│   │   ├── routes/        # API routes
│   │   ├── services/      # Business logic
│   │   └── scraper/       # Scraping logic
│   ├── package.json       # API dependencies
│   └── pnpm-lock.yaml     # Lock file
├── docs/                   # Documentation
│   └── API_REFERENCE.md    # API endpoint documentation
├── scripts/                # Utility scripts
│   ├── claude_scraper.py   # Intelligent search and content analysis
│   └── crawl.py           # Full site archival
├── .env.example           # Example environment variables for Python scripts
├── README.md              # Project overview
└── requirements.txt       # Python dependencies
```

## Scripts Overview

### 1. `claude_scraper.py` - Intelligent Search & Content Analysis

- **Purpose**: Unified tool for web content extraction and analysis
- **Modes**:

  1. **Basic Search**: Quick information finding

     - Uses Claude AI for search optimization
     - Best for simple queries where first match is sufficient
     - Combines site mapping and targeted scraping

  2. **Deep Search**: Advanced multi-mode search with three sub-types:

     - **Quick**: Fast search using map endpoint (same as Basic Search)
     - **Deep**: Analyzes top 5 pages with relevance scoring
       - Content relevance scoring (0-100)
       - Key points extraction
       - Results sorted by relevance
     - **Selective**: Smart CSS selector-based extraction
       - Auto-generates optimal CSS selectors
       - Extracts specific content elements
       - Best for structured data (prices, specs, etc.)

  3. **Analyze**: Single page deep analysis

     - Structured JSON output with metadata
     - Intelligent content organization
     - Markdown formatting preservation

  4. **Batch**: Process multiple URLs in parallel

     - Parallel content extraction
     - Consistent output format
     - Automatic error handling

  5. **Extract**: Custom content extraction
     - User-defined CSS selectors
     - Targeted content extraction
     - Flexible output structure

- **API Usage**: Utilizes multiple endpoints (`map`, `scrape`, `batch/scrape`, `extract`)
- **Best For**: All content extraction needs from quick searches to detailed analysis

### 2. `crawl.py` - Full Website Archival

- **Purpose**: Bulk website crawling and content archiving
- **Key Features**:
  - English language filtering
  - URL deduplication
  - Progress tracking
  - File system organization
- **API Usage**: `crawl` endpoint
- **Best For**: Archiving entire websites or sections

## Key Differences Between Modes

| Feature          | Basic Search | Deep Search | Analyze | Batch  | Extract  |
| ---------------- | ------------ | ----------- | ------- | ------ | -------- |
| Speed            | Fast         | Slow        | Medium  | Fast   | Fast     |
| Depth            | Surface      | Deep        | Deep    | Medium | Targeted |
| Multiple Pages   | Yes          | Yes         | No      | Yes    | No       |
| AI Analysis      | Basic        | Advanced    | Basic   | Basic  | No       |
| Custom Selectors | No           | Optional    | No      | No     | Yes      |
| Best For         | Quick Info   | Research    | Details | Bulk   | Specific |

## Usage Examples

### Intelligent Search & Analysis

```bash
python claude_scraper.py
# Select mode:
# 1. Search - Basic search for quick information
# 2. Analyze - Detailed single page analysis
# 3. Batch - Process multiple URLs in parallel
# 4. Extract - Extract specific content using selectors
# 5. Deep Search - Advanced search with multiple options
#    - Quick: Fast search for simple queries
#    - Deep: Detailed analysis of multiple pages
#    - Selective: Smart selector-based extraction
```

### Full Site Crawl

```bash
python crawl.py <url>
```

## Output Formats

1. **Basic/Quick Search**:

   ```json
   {
     "source_url": "URL where information was found",
     "relevant_info": "Extracted content",
     "search_type": "quick",
     "search_parameter": "Used search term"
   }
   ```

2. **Deep Search**:

   ```json
   {
     "search_type": "deep",
     "results": [
       {
         "url": "Page URL",
         "content": "Extracted content",
         "analysis": {
           "relevance_score": 85,
           "key_points": ["Point 1", "Point 2"],
           "matches_objective": true
         }
       }
     ],
     "total_analyzed": 5
   }
   ```

3. **Selective Search**:

   ```json
   {
     "search_type": "selective",
     "selectors_used": {
       "title": "h1.main-title",
       "price": ".product-price"
     },
     "results": [
       {
         "url": "Page URL",
         "extracted_content": {
           "title": "Found title",
           "price": "Found price"
         }
       }
     ]
   }
   ```

4. **Analyze Mode**:

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

5. **Batch Mode**:

   ```json
   [
     {
       "url": "Page URL",
       "title": "Page title",
       "content": "Processed content",
       "metadata": { ... }
     }
   ]
   ```

6. **Extract Mode**:

   ```json
   {
     "title": "Content matching title selector",
     "content": "Content matching content selector",
     "custom_field": "Content matching custom selector"
   }
   ```

7. **crawl.py**:
   Creates a directory structure:
   ```txt
   crawls/
   └── domain.com/
       ├── page1.md
       ├── page2.md
       └── visited_urls.txt
   ```

## Setup

### Python Scripts

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

### API Setup (using pnpm)

> **Important**: The API project specifically uses pnpm and is not configured for npm. Please use pnpm for dependency management.

1. Install pnpm if you haven't already:

   ```bash
   # Using npm
   npm install -g pnpm
   # Or using Homebrew on macOS
   brew install pnpm
   ```

2. Install API dependencies:

   ```bash
   cd api
   pnpm install
   ```

3. Start the API in development mode:

   ```bash
   pnpm start:dev
   ```

Common API commands (always use pnpm, not npm):

- `pnpm start:dev` - Start development server with hot reload
- `pnpm build` - Build the project
- `pnpm test` - Run tests
- `pnpm format` - Format code using Prettier
- `pnpm add <package>` - Add a new dependency
- `pnpm remove <package>` - Remove a dependency

### Environment Setup

1. Set up environment variables:

   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. Required API keys:
   - `FIRECRAWL_API_KEY` - For FireCrawl API access
   - `ANTHROPIC_API_KEY` - For Claude AI integration (not needed for crawl.py)

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
