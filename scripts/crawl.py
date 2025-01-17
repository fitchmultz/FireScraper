import argparse
import hashlib
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse

import requests


@dataclass
class CrawlConfig:
    """Configuration for crawl behavior."""

    url: str
    max_depth: int = 10
    allow_external: bool = False
    allow_subdomains: bool = True
    languages: Set[str] = None  # None means all languages
    exclude_patterns: List[str] = None  # URL patterns to exclude
    include_patterns: List[str] = None  # URL patterns to include
    timeout: int = 30000  # milliseconds
    max_pages: Optional[int] = None
    save_raw_html: bool = False
    output_dir: Optional[str] = None
    check_interval: int = 5  # seconds between status checks

    def __post_init__(self):
        # Initialize sets/lists if None
        if self.languages is None:
            self.languages = {"en"}
        if self.exclude_patterns is None:
            self.exclude_patterns = []
        if self.include_patterns is None:
            self.include_patterns = []

        # Set output directory if not specified
        if self.output_dir is None:
            domain = urlparse(self.url).netloc
            self.output_dir = f"crawls/{domain}"

    def to_api_params(self) -> dict:
        """Convert config to API parameters."""
        return {
            "url": self.url,
            "allowExternalLinks": self.allow_external,
            "allowSubdomains": self.allow_subdomains,
            "maxDepth": self.max_depth,
            "timeout": self.timeout,
            "limit": self.max_pages,
            "excludePatterns": self.exclude_patterns,
            "includePatterns": self.include_patterns,
        }


def is_english_page(url: str, metadata: dict, config: CrawlConfig) -> bool:
    """Check if a page matches the language requirements."""
    if not config.languages:  # If no languages specified, accept all
        return True

    # Check URL for language codes
    for lang in config.languages:
        if f"-{lang}" in url:
            return True

    # Check metadata language if available
    if metadata and metadata.get("language"):
        return any(
            metadata.get("language").startswith(lang) for lang in config.languages
        )

    return True  # Default to accepting if no language info found


def get_safe_filename(url_path: str) -> str:
    """Generate a safe filename from URL path."""
    # Clean up the filename
    filename = url_path.strip("/").replace("/", "-") or "index"
    # Hash long filenames to avoid issues with file system limits
    if len(filename) > 200:
        filename = hashlib.md5(filename.encode()).hexdigest()
    return f"{filename}.md"


def save_page(
    output_dir: Path, url: str, content: str, metadata: dict, config: CrawlConfig
) -> bool:
    """Save a single page to disk."""
    # Skip pages that don't match language requirements
    if not is_english_page(url, metadata, config):
        print(f"Skipped non-matching language page: {url}")
        return False

    url_path = urlparse(url).path
    filename = get_safe_filename(url_path)
    filepath = output_dir / filename

    # Don't overwrite existing files
    if filepath.exists():
        print(f"Skipped existing file {filename}")
        return False

    # Save markdown content
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    # Optionally save raw HTML
    if config.save_raw_html and "rawHtml" in metadata:
        html_filepath = output_dir / f"{filename}.html"
        with open(html_filepath, "w", encoding="utf-8") as f:
            f.write(metadata["rawHtml"])

    print(f"Saved {filename}")
    return True


def save_visited_urls(output_dir: Path, visited_urls: set):
    """Save list of visited URLs."""
    with open(output_dir / "visited_urls.txt", "w", encoding="utf-8") as f:
        for url in sorted(visited_urls):
            f.write(f"{url}\n")


def crawl_and_save(config: CrawlConfig):
    """Crawl website and save content based on configuration."""
    print(f"Starting crawl of {config.url} with configuration:")
    print(json.dumps(config.to_api_params(), indent=2))

    # Make the crawl request with configured parameters
    response = requests.post(
        "http://localhost:3002/v1/crawl", json=config.to_api_params()
    )

    if not response.ok:
        print(f"Error making crawl request: {response.text}")
        return

    print(f"Crawl request successful: {response.text}")
    crawl_id = response.json()["id"]

    # Create output directory
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created output directory: {output_dir}")

    # Track progress
    saved_count = 0
    visited_urls = set()
    last_status = None
    skipped_count = 0

    # Wait for crawling to complete with progress updates
    print("Waiting for crawl to complete...")
    while True:
        results = requests.get(f"http://localhost:3002/v1/crawl/{crawl_id}")
        if not results.ok:
            print(f"Error checking status: {results.text}")
            return

        status = results.json()

        # Save new pages as they're completed
        if "data" in status:
            for item in status["data"]:
                if "markdown" in item and "metadata" in item:
                    url = item["metadata"]["url"]
                    if url not in visited_urls:
                        if save_page(
                            output_dir, url, item["markdown"], item["metadata"], config
                        ):
                            saved_count += 1
                        else:
                            skipped_count += 1
                        visited_urls.add(url)

        # Show progress
        current_status = (status.get("completed", 0), status.get("total", 0))
        if current_status != last_status:
            print(
                f"Progress: {current_status[0]}/{current_status[1]} pages crawled... ({saved_count} saved, {skipped_count} skipped)"
            )
            last_status = current_status

        if status.get("status") == "completed":
            break

        time.sleep(config.check_interval)

    # Save final list of visited URLs
    save_visited_urls(output_dir, visited_urls)
    print(f"\nFinished! Saved {saved_count} files to {output_dir}")
    print(f"Skipped {skipped_count} non-matching or duplicate pages")
    print(f"Total unique URLs visited: {len(visited_urls)}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Crawl and save website content with configurable options."
    )

    parser.add_argument("url", help="The website URL to crawl")

    # Crawl behavior
    parser.add_argument(
        "--max-depth", type=int, default=10, help="Maximum depth to crawl (default: 10)"
    )
    parser.add_argument(
        "--max-pages", type=int, help="Maximum number of pages to crawl"
    )
    parser.add_argument(
        "--allow-external", action="store_true", help="Allow crawling external links"
    )
    parser.add_argument(
        "--no-subdomains",
        action="store_false",
        dest="allow_subdomains",
        help="Don't crawl subdomains",
    )

    # Content filtering
    parser.add_argument(
        "--languages",
        nargs="+",
        default=["en"],
        help="Languages to include (e.g., en es fr). Default: en",
    )
    parser.add_argument("--exclude", nargs="+", help="URL patterns to exclude")
    parser.add_argument("--include", nargs="+", help="URL patterns to include")

    # Output options
    parser.add_argument(
        "--output-dir", help="Custom output directory (default: crawls/<domain>)"
    )
    parser.add_argument(
        "--save-html", action="store_true", help="Also save raw HTML content"
    )
    parser.add_argument(
        "--check-interval",
        type=int,
        default=5,
        help="Seconds between progress checks (default: 5)",
    )

    # API options
    parser.add_argument(
        "--timeout",
        type=int,
        default=30000,
        help="API timeout in milliseconds (default: 30000)",
    )

    args = parser.parse_args()

    # Convert args to CrawlConfig
    config = CrawlConfig(
        url=args.url,
        max_depth=args.max_depth,
        allow_external=args.allow_external,
        allow_subdomains=args.allow_subdomains,
        languages=set(args.languages),
        exclude_patterns=args.exclude,
        include_patterns=args.include,
        timeout=args.timeout,
        max_pages=args.max_pages,
        save_raw_html=args.save_html,
        output_dir=args.output_dir,
        check_interval=args.check_interval,
    )

    return config


if __name__ == "__main__":
    config = parse_args()
    crawl_and_save(config)
