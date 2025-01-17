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


# ANSI color codes for better readability
class Colors:
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


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
        params = {
            "url": self.url,
            "maxDepth": self.max_depth,
            "allowSubdomains": self.allow_subdomains,
            "limit": (
                self.max_pages if self.max_pages is not None else 1000000
            ),  # Use large number for "unlimited"
            "allowExternalLinks": self.allow_external,  # API expects 'allowExternalLinks' not 'allowExternal'
        }

        # Only include optional patterns if they have values
        if self.exclude_patterns:
            params["excludePatterns"] = self.exclude_patterns
        if self.include_patterns:
            params["includePatterns"] = self.include_patterns

        return params

    def display_config(self):
        """Display current configuration in a user-friendly format."""
        print(f"\n{Colors.BLUE}Crawl Configuration:{Colors.RESET}")
        print(f"  {Colors.CYAN}URL:{Colors.RESET} {self.url}")
        print(f"  {Colors.CYAN}Max Depth:{Colors.RESET} {self.max_depth}")
        print(
            f"  {Colors.CYAN}Max Pages:{Colors.RESET} {self.max_pages or 'Unlimited'}"
        )
        print(
            f"  {Colors.CYAN}External Links:{Colors.RESET} {'Allowed' if self.allow_external else 'Disallowed'}"
        )
        print(
            f"  {Colors.CYAN}Subdomains:{Colors.RESET} {'Allowed' if self.allow_subdomains else 'Disallowed'}"
        )
        print(
            f"  {Colors.CYAN}Languages:{Colors.RESET} {', '.join(self.languages) if self.languages else 'All'}"
        )
        if self.exclude_patterns:
            print(
                f"  {Colors.CYAN}Excluded Patterns:{Colors.RESET} {', '.join(self.exclude_patterns)}"
            )
        if self.include_patterns:
            print(
                f"  {Colors.CYAN}Included Patterns:{Colors.RESET} {', '.join(self.include_patterns)}"
            )
        print(f"  {Colors.CYAN}Output Directory:{Colors.RESET} {self.output_dir}")
        print(
            f"  {Colors.CYAN}Save HTML:{Colors.RESET} {'Yes' if self.save_raw_html else 'No'}\n"
        )

    @classmethod
    def from_interactive(cls):
        """Create configuration from interactive user input."""
        print(f"\n{Colors.BLUE}=== Web Crawler Configuration ==={Colors.RESET}")

        # Get required URL
        while True:
            url = input(
                f"\n{Colors.CYAN}Enter website URL to crawl:{Colors.RESET} "
            ).strip()

            # Silently add https:// if no protocol specified
            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"

            try:
                # Test if URL is reachable
                response = requests.head(url, timeout=5)
                if (
                    response.ok or response.status_code == 405
                ):  # 405 = Method not allowed but URL exists
                    break

                # If https:// fails, try http:// silently
                if url.startswith("https://"):
                    http_url = url.replace("https://", "http://")
                    response = requests.head(http_url, timeout=5)
                    if response.ok or response.status_code == 405:
                        url = http_url
                        break

                print(
                    f"{Colors.RED}Could not access URL. Please check the URL and try again.{Colors.RESET}"
                )
            except requests.exceptions.RequestException:
                print(
                    f"{Colors.RED}Could not connect to URL. Please check the URL and try again.{Colors.RESET}"
                )

        # Crawl Behavior
        print(f"\n{Colors.MAGENTA}=== Crawl Behavior ==={Colors.RESET}")
        max_depth = int(
            input(f"{Colors.CYAN}Maximum crawl depth (default 10):{Colors.RESET} ")
            or "10"
        )
        max_pages = input(
            f"{Colors.CYAN}Maximum pages to crawl (Enter for unlimited):{Colors.RESET} "
        ).strip()
        max_pages = int(max_pages) if max_pages else None

        allow_external = (
            input(f"{Colors.CYAN}Allow external links? (y/N):{Colors.RESET} ")
            .lower()
            .startswith("y")
        )
        allow_subdomains = (
            input(f"{Colors.CYAN}Allow subdomains? (Y/n):{Colors.RESET} ").lower()
            != "n"
        )

        # Content Filtering
        print(f"\n{Colors.MAGENTA}=== Content Filtering ==={Colors.RESET}")
        languages_input = input(
            f"{Colors.CYAN}Languages to include (space-separated, default 'en'):{Colors.RESET} "
        ).strip()
        languages = set(languages_input.split()) if languages_input else {"en"}

        exclude_input = input(
            f"{Colors.CYAN}URL patterns to exclude (space-separated, e.g., '/blog/* /archive/*'):{Colors.RESET} "
        ).strip()
        exclude_patterns = exclude_input.split() if exclude_input else None

        include_input = input(
            f"{Colors.CYAN}URL patterns to include (space-separated, e.g., '/docs/*'):{Colors.RESET} "
        ).strip()
        include_patterns = include_input.split() if include_input else None

        # Output Options
        print(f"\n{Colors.MAGENTA}=== Output Options ==={Colors.RESET}")
        output_dir = (
            input(
                f"{Colors.CYAN}Output directory (Enter for default 'crawls/<domain>'):{Colors.RESET} "
            ).strip()
            or None
        )
        save_raw_html = (
            input(f"{Colors.CYAN}Save raw HTML? (y/N):{Colors.RESET} ")
            .lower()
            .startswith("y")
        )

        check_interval = int(
            input(
                f"{Colors.CYAN}Progress check interval in seconds (default 5):{Colors.RESET} "
            )
            or "5"
        )

        # Advanced Options
        print(f"\n{Colors.MAGENTA}=== Advanced Options ==={Colors.RESET}")
        timeout = int(
            input(
                f"{Colors.CYAN}API timeout in milliseconds (default 30000):{Colors.RESET} "
            )
            or "30000"
        )

        return cls(
            url=url,
            max_depth=max_depth,
            allow_external=allow_external,
            allow_subdomains=allow_subdomains,
            languages=languages,
            exclude_patterns=exclude_patterns,
            include_patterns=include_patterns,
            timeout=timeout,
            max_pages=max_pages,
            save_raw_html=save_raw_html,
            output_dir=output_dir,
            check_interval=check_interval,
        )


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
        print(f"{Colors.YELLOW}Skipped non-matching language page: {url}{Colors.RESET}")
        return False

    url_path = urlparse(url).path
    filename = get_safe_filename(url_path)
    filepath = output_dir / filename

    # Don't overwrite existing files
    if filepath.exists():
        print(f"{Colors.YELLOW}Skipped existing file {filename}{Colors.RESET}")
        return False

    try:
        # Save markdown content
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # Optionally save raw HTML
        if config.save_raw_html and "rawHtml" in metadata:
            html_filepath = output_dir / f"{filename}.html"
            with open(html_filepath, "w", encoding="utf-8") as f:
                f.write(metadata["rawHtml"])

        print(f"{Colors.GREEN}Saved {filename}{Colors.RESET}")
        return True
    except Exception as e:
        print(f"{Colors.RED}Error saving {filename}: {str(e)}{Colors.RESET}")
        return False


def save_visited_urls(output_dir: Path, visited_urls: set):
    """Save list of visited URLs."""
    with open(output_dir / "visited_urls.txt", "w", encoding="utf-8") as f:
        for url in sorted(visited_urls):
            f.write(f"{url}\n")


def crawl_and_save(config: CrawlConfig):
    """Crawl website and save content based on configuration."""
    config.display_config()
    print(f"{Colors.BLUE}Starting crawl of {config.url}{Colors.RESET}")

    try:
        # Make the crawl request with configured parameters
        print(f"{Colors.YELLOW}Initiating crawl request...{Colors.RESET}")
        response = requests.post(
            "http://localhost:3002/v1/crawl", json=config.to_api_params()
        )

        if not response.ok:
            print(
                f"{Colors.RED}Error making crawl request: {response.text}{Colors.RESET}"
            )
            return

        print(f"{Colors.GREEN}Crawl request successful!{Colors.RESET}")
        crawl_id = response.json()["id"]

        # Create output directory
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"{Colors.GREEN}Created output directory: {output_dir}{Colors.RESET}")

        # Track progress
        saved_count = 0
        visited_urls = set()
        last_status = None
        skipped_count = 0
        error_count = 0

        # Wait for crawling to complete with progress updates
        print(f"\n{Colors.BLUE}Crawling in progress...{Colors.RESET}")
        start_time = time.time()

        try:
            while True:
                results = requests.get(f"http://localhost:3002/v1/crawl/{crawl_id}")
                if not results.ok:
                    print(
                        f"{Colors.RED}Error checking status: {results.text}{Colors.RESET}"
                    )
                    return

                status = results.json()

                # Save new pages as they're completed
                if "data" in status:
                    for item in status["data"]:
                        if "markdown" in item and "metadata" in item:
                            url = item["metadata"]["url"]
                            if url not in visited_urls:
                                try:
                                    if save_page(
                                        output_dir,
                                        url,
                                        item["markdown"],
                                        item["metadata"],
                                        config,
                                    ):
                                        saved_count += 1
                                    else:
                                        skipped_count += 1
                                except Exception as e:
                                    print(
                                        f"{Colors.RED}Error processing {url}: {str(e)}{Colors.RESET}"
                                    )
                                    error_count += 1
                                visited_urls.add(url)

                # Show progress with percentage
                current_status = (status.get("completed", 0), status.get("total", 0))
                if current_status != last_status:
                    completed, total = current_status
                    if total > 0:
                        percentage = (completed / total) * 100
                        elapsed_time = time.time() - start_time
                        pages_per_second = (
                            completed / elapsed_time if elapsed_time > 0 else 0
                        )

                        print(
                            f"{Colors.CYAN}Progress: {completed}/{total} pages ({percentage:.1f}%) - "
                            f"Rate: {pages_per_second:.1f} pages/sec{Colors.RESET}"
                        )
                        print(
                            f"{Colors.GREEN}Saved: {saved_count} | "
                            f"{Colors.YELLOW}Skipped: {skipped_count} | "
                            f"{Colors.RED}Errors: {error_count}{Colors.RESET}"
                        )
                    last_status = current_status

                if status.get("status") == "completed":
                    break

                time.sleep(config.check_interval)

        except KeyboardInterrupt:
            print(
                f"\n{Colors.YELLOW}Crawl interrupted by user. Saving progress...{Colors.RESET}"
            )

        finally:
            # Save final list of visited URLs
            save_visited_urls(output_dir, visited_urls)
            elapsed_time = time.time() - start_time

            print(f"\n{Colors.MAGENTA}Crawl Summary:{Colors.RESET}")
            print(f"  {Colors.GREEN}✓ Saved: {saved_count} files{Colors.RESET}")
            print(f"  {Colors.YELLOW}⚠ Skipped: {skipped_count} pages{Colors.RESET}")
            print(f"  {Colors.RED}✗ Errors: {error_count} pages{Colors.RESET}")
            print(f"  {Colors.BLUE}• Total URLs: {len(visited_urls)}{Colors.RESET}")
            print(
                f"  {Colors.BLUE}• Time taken: {elapsed_time:.1f} seconds{Colors.RESET}"
            )
            print(
                f"  {Colors.BLUE}• Average speed: {len(visited_urls)/elapsed_time:.1f} pages/sec{Colors.RESET}"
            )
            print(f"  {Colors.GREEN}• Output directory: {output_dir}{Colors.RESET}\n")

    except Exception as e:
        print(f"{Colors.RED}Fatal error: {str(e)}{Colors.RESET}")
        sys.exit(1)


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


def main():
    """Main entry point with interactive or command-line modes."""
    if len(sys.argv) > 1:
        # Use command-line mode if arguments are provided
        config = parse_args()
    else:
        # Use interactive mode if no arguments
        print(f"\n{Colors.GREEN}Welcome to the Web Crawler!{Colors.RESET}")
        print(
            f"{Colors.BLUE}No command-line arguments detected. Starting interactive mode...{Colors.RESET}"
        )
        print(
            f"{Colors.YELLOW}Tip: Use command-line arguments for automated/scripted usage.{Colors.RESET}"
        )
        config = CrawlConfig.from_interactive()

    crawl_and_save(config)


if __name__ == "__main__":
    main()
