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

- **Purpose**: Unified tool for targeted search and content analysis
- **Modes**:
  1. **Search Mode**: Find specific information across multiple pages
     - Uses Claude AI for search optimization
     - Combines site mapping and targeted scraping
     - Extracts specific information based on user objectives
  2. **Analyze Mode**: Deep content extraction from single pages
     - Structured JSON output with metadata
     - Intelligent content organization
     - Markdown formatting preservation
- **API Usage**: `map` and `scrape` endpoints
- **Best For**: Both targeted searches and detailed page analysis

### 2. `crawl.py` - Full Website Archival

- **Purpose**: Bulk website crawling and content archiving
- **Key Features**:
  - English language filtering
  - URL deduplication
  - Progress tracking
  - File system organization
- **API Usage**: `crawl` endpoint
- **Best For**: Archiving entire websites or sections

## Key Differences

| Feature        | claude_scraper.py (Search) | claude_scraper.py (Analyze) | crawl.py       |
| -------------- | -------------------------- | --------------------------- | -------------- |
| API Endpoints  | map + scrape               | scrape only                 | crawl          |
| AI Integration | Search & Analysis          | Content Structuring         | None           |
| Scope          | Targeted Search            | Single Page                 | Full Site      |
| Output         | Specific Information       | Structured JSON             | Markdown Files |
| Storage        | Memory                     | Memory                      | File System    |

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

## Usage Examples

### Intelligent Search & Analysis

```bash
python claude_scraper.py
# Select mode:
# 1. Search - Find specific information across pages
# 2. Analyze - Detailed analysis of a single page
# Follow the prompts to enter URL and objectives
```

### Full Site Crawl

```bash
python crawl.py <url>
```

## Output Formats

1. **claude_scraper.py (Search Mode)**:

   ```json
   {
     "relevant_info": "Extracted information matching objective",
     "source_url": "URL where information was found"
   }
   ```

2. **claude_scraper.py (Analyze Mode)**:

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
   Creates a directory structure:

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
