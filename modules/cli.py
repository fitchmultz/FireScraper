"""Command-line interface for FireScraper."""

import argparse
from typing import Any


def setup_crawl_parser(subparsers: Any) -> None:
    """Set up the crawl command parser."""
    crawl_parser = subparsers.add_parser(
        "crawl", help="Crawl a website and save its content"
    )
    crawl_parser.add_argument("url", help="Website URL to crawl")
    crawl_parser.add_argument(
        "--max-depth", type=int, default=10, help="Maximum crawl depth"
    )
    crawl_parser.add_argument(
        "--max-pages", type=int, help="Maximum number of pages to crawl"
    )
    crawl_parser.add_argument(
        "--allow-external",
        action="store_true",
        help="Allow crawling external links",
    )
    crawl_parser.add_argument(
        "--no-subdomains",
        action="store_false",
        dest="allow_subdomains",
        help="Disallow crawling subdomains",
    )
    crawl_parser.add_argument(
        "--languages",
        nargs="+",
        default=["en"],
        help="Languages to include (space-separated)",
    )
    crawl_parser.add_argument(
        "--exclude",
        nargs="+",
        help="URL patterns to exclude (space-separated)",
        dest="exclude_patterns",
    )
    crawl_parser.add_argument(
        "--include",
        nargs="+",
        help="URL patterns to include (space-separated)",
        dest="include_patterns",
    )
    crawl_parser.add_argument(
        "--output-dir", help="Output directory (default: crawls/<domain>)"
    )
    crawl_parser.add_argument(
        "--save-html", action="store_true", help="Save raw HTML files"
    )
    crawl_parser.add_argument(
        "--check-interval",
        type=int,
        default=5,
        help="Progress check interval in seconds",
    )
    crawl_parser.add_argument(
        "--timeout",
        type=int,
        default=30000,
        help="API timeout in milliseconds",
    )


def setup_search_parser(subparsers: Any) -> None:
    """Set up the search command parser."""
    search_parser = subparsers.add_parser(
        "search", help="Search through crawled content"
    )
    search_parser.add_argument("url", help="Website URL to search")
    search_parser.add_argument("objective", help="Search objective or query")
    search_parser.add_argument(
        "--type",
        choices=["quick", "deep", "selective"],
        default="quick",
        help="Type of search to perform",
    )


def setup_analyze_parser(subparsers: Any) -> None:
    """Set up the analyze command parser."""
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a single page")
    analyze_parser.add_argument("url", help="URL to analyze")


def setup_batch_parser(subparsers: Any) -> None:
    """Set up the batch command parser."""
    batch_parser = subparsers.add_parser(
        "batch", help="Process multiple URLs in parallel"
    )
    batch_parser.add_argument("urls", nargs="+", help="List of URLs to process")


def setup_extract_parser(subparsers: Any) -> None:
    """Set up the extract command parser."""
    extract_parser = subparsers.add_parser(
        "extract", help="Extract specific content using selectors"
    )
    extract_parser.add_argument("url", help="URL to extract from")
    extract_parser.add_argument(
        "--selectors",
        type=str,
        required=True,
        help='JSON string of selectors (e.g., \'{"title": "h1", "content": ".main-content"}\')',
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="FireScraper - A unified web scraping and analysis tool"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    setup_crawl_parser(subparsers)
    setup_search_parser(subparsers)
    setup_analyze_parser(subparsers)
    setup_batch_parser(subparsers)
    setup_extract_parser(subparsers)

    return parser.parse_args()
