import hashlib
import json
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests


def is_english_page(url, metadata):
    """Check if a page is in English by examining URL and metadata"""
    # Skip pages with language codes in URL
    if "-zh" in url or "-es" in url or "-fr" in url:
        return False

    # Check metadata language if available
    if metadata and metadata.get("language"):
        return metadata.get("language").startswith("en")

    return True


def get_safe_filename(url_path):
    """Generate a safe filename from URL path"""
    # Clean up the filename
    filename = url_path.strip("/").replace("/", "-") or "index"
    # Hash long filenames to avoid issues with file system limits
    if len(filename) > 200:
        filename = hashlib.md5(filename.encode()).hexdigest()
    return f"{filename}.md"


def save_page(output_dir, url, content, metadata):
    """Save a single page to disk"""
    # Skip non-English pages
    if not is_english_page(url, metadata):
        print(f"Skipped non-English page: {url}")
        return False

    url_path = urlparse(url).path
    filename = get_safe_filename(url_path)
    filepath = output_dir / filename

    # Don't overwrite existing files
    if filepath.exists():
        print(f"Skipped existing file {filename}")
        return False

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved {filename}")
    return True


def save_visited_urls(output_dir, visited_urls):
    """Save list of visited URLs"""
    with open(output_dir / "visited_urls.txt", "w", encoding="utf-8") as f:
        for url in sorted(visited_urls):
            f.write(f"{url}\n")


def crawl_and_save(url):
    print(f"Starting crawl of {url}")

    # Make the crawl request with supported parameters
    response = requests.post(
        "http://localhost:3002/v1/crawl",
        json={
            "url": url,
            "allowExternalLinks": False,
            "allowSubdomains": True,
            "maxDepth": 10,  # Increased depth to follow pagination
        },
    )

    if not response.ok:
        print(f"Error making crawl request: {response.text}")
        return

    print(f"Crawl request successful: {response.text}")
    crawl_id = response.json()["id"]

    # Create output directory based on domain
    domain = urlparse(url).netloc
    output_dir = Path(f"crawls/{domain}")
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
                            output_dir, url, item["markdown"], item["metadata"]
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

        time.sleep(5)  # Check every 5 seconds

    # Save final list of visited URLs
    save_visited_urls(output_dir, visited_urls)
    print(f"\nFinished! Saved {saved_count} files to {output_dir}")
    print(f"Skipped {skipped_count} non-English or duplicate pages")
    print(f"Total unique URLs visited: {len(visited_urls)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python crawl.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    crawl_and_save(url)
