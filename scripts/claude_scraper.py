import json
import os
from enum import Enum
from typing import Dict, List, Optional

from anthropic import Anthropic
from dotenv import load_dotenv
from firecrawl import FirecrawlApp


class Mode(Enum):
    SEARCH = "search"  # Intelligent search across site
    ANALYZE = "analyze"  # Single page analysis


# ANSI color codes
class Colors:
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


class ClaudeScraper:
    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Model configuration
        self.max_tokens = int(os.getenv("MAX_TOKENS", "8192"))
        self.model_name = os.getenv("ANTHROPIC_MODEL_NAME", "claude-3-5-haiku-latest")

        # Initialize clients
        self.app = FirecrawlApp(
            api_key=os.getenv("FIRECRAWL_API_KEY"), api_url="http://localhost:3002"
        )
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def find_relevant_pages(self, objective: str, url: str) -> Optional[List[str]]:
        """Find pages that most likely contain the objective."""
        try:
            print(
                f"{Colors.CYAN}Understood. The objective is: {objective}{Colors.RESET}"
            )
            print(f"{Colors.CYAN}Initiating search on the website: {url}{Colors.RESET}")

            map_prompt = f"""
            The map function generates a list of URLs from a website and it accepts a search parameter. Based on the objective of: {objective}, come up with a 1-2 word search parameter that will help us find the information we need. Only respond with 1-2 words nothing else.
            """

            print(
                f"{Colors.YELLOW}Analyzing objective to determine optimal search parameter...{Colors.RESET}"
            )
            completion = self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=0,
                system="You are an expert web crawler. Respond with the BEST search parameter.",
                messages=[{"role": "user", "content": map_prompt}],
            )

            map_search_parameter = completion.content[0].text
            print(
                f"{Colors.GREEN}Optimal search parameter identified: {map_search_parameter}{Colors.RESET}"
            )

            print(
                f"{Colors.YELLOW}Mapping website using the identified search parameter...{Colors.RESET}"
            )
            map_website = self.app.map_url(url, params={"search": map_search_parameter})
            print(
                f"{Colors.GREEN}Website mapping completed successfully.{Colors.RESET}"
            )
            print(
                f"{Colors.GREEN}Located {len(map_website['links'])} relevant links.{Colors.RESET}"
            )

            return map_website["links"]
        except Exception as e:
            print(
                f"{Colors.RED}Error during page identification: {str(e)}{Colors.RESET}"
            )
            return None

    def analyze_content(self, url: str) -> Optional[Dict]:
        """Extract and format content from a webpage."""
        try:
            print(f"{Colors.CYAN}Scraping content from: {url}{Colors.RESET}")

            # Scrape the page with JavaScript rendering
            print(f"{Colors.YELLOW}Fetching page content...{Colors.RESET}")
            result = self.app.scrape_url(url, {"formats": ["markdown"]})
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

            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=0,
                system="You are an EXPERT at extracting and structuring webpage content. Output ONLY valid, properly ESCAPED JSON with NO additional text.",
                messages=[{"role": "user", "content": prompt}],
            )

            try:
                return json.loads(response.content[0].text)
            except json.JSONDecodeError as e:
                print(
                    f"{Colors.RED}Error parsing JSON response: {str(e)}{Colors.RESET}"
                )
                raise

        except Exception as e:
            print(f"{Colors.RED}Error processing content: {str(e)}{Colors.RESET}")
            return None

    def search_content(self, objective: str, url: str) -> Optional[Dict]:
        """Search for specific content across pages."""
        try:
            # Find relevant pages
            map_website = self.find_relevant_pages(objective, url)
            if not map_website:
                return None

            # Get top 2 links from the map result
            top_links = map_website[:2]
            print(
                f"{Colors.CYAN}Proceeding to analyze top {len(top_links)} links: {top_links}{Colors.RESET}"
            )

            # Analyze each page
            for url in top_links:
                try:
                    result = self.app.scrape_url(
                        url, {"formats": ["markdown"], "timeout": 30000}
                    )
                    check_prompt = f"""
                    Given the following scraped content and objective, determine if the objective is met.
                    If it is, extract the relevant information in a simple and concise JSON format. Use only the necessary fields and avoid nested structures if possible.
                    If the objective is not met with confidence, respond with 'Objective not met'.

                    Objective: {objective}
                    Scraped content: {result['markdown']}

                    Remember:
                    1. Only return JSON if you are confident the objective is fully met.
                    2. Keep the JSON structure as simple and flat as possible.
                    3. Do not include any explanations or markdown formatting in your response.
                    """

                    completion = self.client.messages.create(
                        model=self.model_name,
                        max_tokens=1000,
                        temperature=0,
                        system="You are an expert web crawler. Respond with the relevant information in JSON format.",
                        messages=[{"role": "user", "content": check_prompt}],
                    )

                    result = completion.content[0].text
                    if result != "Objective not met":
                        try:
                            return json.loads(result)
                        except json.JSONDecodeError:
                            print(
                                f"{Colors.RED}Error parsing response. Proceeding to next page...{Colors.RESET}"
                            )
                except Exception as e:
                    print(f"{Colors.RED}Error processing {url}: {str(e)}{Colors.RESET}")
                    continue

            print(
                f"{Colors.RED}All available pages analyzed. Objective not fulfilled.{Colors.RESET}"
            )
            return None

        except Exception as e:
            print(f"{Colors.RED}Error during content search: {str(e)}{Colors.RESET}")
            return None

    def process(
        self, mode: Mode, url: str, objective: Optional[str] = None
    ) -> Optional[Dict]:
        """Main processing function that handles both modes."""
        if mode == Mode.SEARCH:
            if not objective:
                raise ValueError("Objective is required for search mode")
            return self.search_content(objective, url)
        else:  # Mode.ANALYZE
            return self.analyze_content(url)


def main():
    """CLI entry point."""
    print(f"{Colors.BLUE}Select mode:{Colors.RESET}")
    print(
        f"1. {Colors.CYAN}Search{Colors.RESET} - Find specific information across pages"
    )
    print(f"2. {Colors.CYAN}Analyze{Colors.RESET} - Detailed analysis of a single page")

    mode_input = input(f"{Colors.BLUE}Enter mode (1 or 2): {Colors.RESET}")
    mode = Mode.SEARCH if mode_input == "1" else Mode.ANALYZE

    url = input(f"{Colors.BLUE}Enter the website URL: {Colors.RESET}")
    if not url.strip():
        url = "https://www.firecrawl.dev/"

    objective = None
    if mode == Mode.SEARCH:
        objective = input(f"{Colors.BLUE}Enter your search objective: {Colors.RESET}")
        if not objective.strip():
            objective = "find me the pricing plans"

    print(f"{Colors.YELLOW}Initiating {mode.value} mode...{Colors.RESET}")

    try:
        scraper = ClaudeScraper()
        result = scraper.process(mode, url, objective)

        if result:
            print(f"\n{Colors.MAGENTA}Results:{Colors.RESET}\n")
            print(f"{Colors.MAGENTA}{json.dumps(result, indent=2)}{Colors.RESET}")
        else:
            print(f"{Colors.RED}No results found.{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error: {str(e)}{Colors.RESET}")
        sys.exit(1)


if __name__ == "__main__":
    import sys

    main()
