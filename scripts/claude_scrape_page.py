import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv
from firecrawl import FirecrawlApp


# ANSI color codes
class Colors:
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


# Load environment variables
load_dotenv()

# Model configuration
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "8192"))
MODEL_NAME = os.getenv("ANTHROPIC_MODEL_NAME", "claude-3-5-haiku-latest")

# Initialize the FirecrawlApp and Anthropic client
app = FirecrawlApp(
    api_key=os.getenv("FIRECRAWL_API_KEY"), api_url="http://localhost:3002"
)
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def extract_content(url: str) -> dict:
    """Extract and format content from a webpage."""
    try:
        print(f"{Colors.CYAN}Scraping content from: {url}{Colors.RESET}")

        # Scrape the page with JavaScript rendering
        print(f"{Colors.YELLOW}Fetching page content...{Colors.RESET}")
        result = app.scrape_url(url, {"formats": ["markdown"]})
        content = result["markdown"]
        print(f"{Colors.GREEN}Page content retrieved successfully.{Colors.RESET}")

        # Use Claude to extract and format
        print(f"{Colors.YELLOW}Processing content with Claude...{Colors.RESET}")
        prompt = f"""
        You are tasked with extracting and structuring the main content from this webpage VERBATIM.

        REQUIREMENTS:
        1. Return a JSON object with EXACTLY this structure:
        {{
            "title": "Main page title",
            "description": "Brief description or summary if available",
            "content": "Main content in PROPER MARKDOWN format",
            "metadata": {{
                "last_updated": "Update date ONLY IF FOUND IN THE PAGE",
                "author": "Author ONLY IF FOUND IN THE PAGE",
                "reading_time": "Estimated reading time in minutes"
            }}
        }}

        2. Content Cleanup:
        - REMOVE all navigation elements, headers, footers, ads, and non-content
        - PRESERVE all important headings, lists, and markdown formatting
        - ONLY include metadata fields that are explicitly present in the content

        3. JSON Formatting:
        - ESCAPE all quotes with \\"
        - ESCAPE newlines with \\n
        - REMOVE all control characters
        - PROPERLY ESCAPE all special characters
        - VALIDATE the final JSON is parseable

        4. Response Format:
        - Output ONLY the valid JSON object
        - NO explanations or additional text
        - NO markdown code blocks or formatting

        Here is the webpage content:
        {content[:199000]}
        """

        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            temperature=0,
            system="You are an EXPERT at extracting and structuring webpage content. Output ONLY valid, properly ESCAPED JSON with NO additional text.",
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            return json.loads(response.content[0].text)
        except json.JSONDecodeError as e:
            print(f"{Colors.RED}Error parsing JSON response: {str(e)}{Colors.RESET}")
            raise

    except Exception as e:
        print(f"{Colors.RED}Error processing content: {str(e)}{Colors.RESET}")
        raise


def main():
    """CLI entry point for the scraper."""
    # Get user input
    url = input(f"{Colors.BLUE}Enter the website to scrape: {Colors.RESET}")
    if not url.strip():
        url = "https://www.firecrawl.dev/"

    print(f"{Colors.YELLOW}Initiating content extraction...{Colors.RESET}")

    try:
        result = extract_content(url)
        print(f"\n{Colors.MAGENTA}Extracted Content:{Colors.RESET}\n")
        print(f"{Colors.MAGENTA}{json.dumps(result, indent=2)}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error: {str(e)}{Colors.RESET}")
        sys.exit(1)


if __name__ == "__main__":
    import sys

    main()
