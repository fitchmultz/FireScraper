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
    BATCH = "batch"  # Process multiple URLs in parallel
    EXTRACT = "extract"  # Extract specific content using selectors
    DEEP_SEARCH = "deep_search"  # Combined search across multiple modes


class SearchType(Enum):
    QUICK = "quick"  # Quick search using map endpoint
    DEEP = "deep"  # Deep search with content analysis
    SELECTIVE = "selective"  # Search with specific content filters


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

    def search_content(
        self, objective: str, url: str, search_type: SearchType = SearchType.QUICK
    ) -> Optional[Dict]:
        """Enhanced search with different search types."""
        try:
            print(
                f"{Colors.CYAN}Initiating {search_type.value} search for: {objective}{Colors.RESET}"
            )
            print(f"{Colors.CYAN}Target website: {url}{Colors.RESET}")

            if search_type == SearchType.QUICK:
                return self._quick_search(objective, url)
            elif search_type == SearchType.DEEP:
                return self._deep_search(objective, url)
            elif search_type == SearchType.SELECTIVE:
                return self._selective_search(objective, url)

        except Exception as e:
            print(f"{Colors.RED}Error during search: {str(e)}{Colors.RESET}")
            return None

    def _quick_search(self, objective: str, url: str) -> Optional[Dict]:
        """Quick search using map endpoint."""
        try:
            map_prompt = f"""
            The map function generates a list of URLs from a website and it accepts a search parameter.
            Based on the objective of: {objective}, come up with a 1-2 word search parameter that will help us find the information we need.
            Only respond with 1-2 words nothing else.
            """

            completion = self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=0,
                system="You are an expert web crawler. Respond with the BEST search parameter.",
                messages=[{"role": "user", "content": map_prompt}],
            )

            map_search_parameter = completion.content[0].text
            print(
                f"{Colors.GREEN}Search parameter: {map_search_parameter}{Colors.RESET}"
            )

            map_website = self.app.map_url(url, params={"search": map_search_parameter})
            if not map_website["links"]:
                return None

            # Get first relevant link and analyze
            target_url = map_website["links"][0]
            result = self.app.scrape_url(target_url, {"formats": ["markdown"]})

            return {
                "source_url": target_url,
                "relevant_info": result["markdown"],
                "search_type": "quick",
                "search_parameter": map_search_parameter,
            }
        except Exception as e:
            print(f"{Colors.RED}Error in quick search: {str(e)}{Colors.RESET}")
            return None

    def _deep_search(self, objective: str, url: str) -> Optional[Dict]:
        """Deep search with content analysis."""
        try:
            # First get potential URLs
            map_website = self.app.map_url(url)
            results = []

            # Analyze top 5 pages in detail
            for target_url in map_website["links"][:5]:
                try:
                    result = self.app.scrape_url(target_url, {"formats": ["markdown"]})

                    # Use Claude to analyze content relevance
                    analysis_prompt = f"""
                    Analyze this content and determine its relevance to the objective: {objective}
                    Return a JSON with these fields:
                    - relevance_score (0-100)
                    - key_points (list of relevant points)
                    - matches_objective (boolean)
                    Only return valid JSON, no other text.

                    Content: {result["markdown"][:5000]}
                    """

                    completion = self.client.messages.create(
                        model=self.model_name,
                        max_tokens=1000,
                        temperature=0,
                        system="You are an expert content analyzer. Return only valid JSON.",
                        messages=[{"role": "user", "content": analysis_prompt}],
                    )

                    analysis = json.loads(completion.content[0].text)
                    if analysis["matches_objective"]:
                        results.append(
                            {
                                "url": target_url,
                                "content": result["markdown"],
                                "analysis": analysis,
                            }
                        )

                except Exception as e:
                    print(
                        f"{Colors.YELLOW}Error analyzing {target_url}: {str(e)}{Colors.RESET}"
                    )
                    continue

            if results:
                # Sort by relevance score
                results.sort(
                    key=lambda x: x["analysis"]["relevance_score"], reverse=True
                )
                return {
                    "search_type": "deep",
                    "results": results,
                    "total_analyzed": len(map_website["links"][:5]),
                }
            return None

        except Exception as e:
            print(f"{Colors.RED}Error in deep search: {str(e)}{Colors.RESET}")
            return None

    def _selective_search(self, objective: str, url: str) -> Optional[Dict]:
        """Search with specific content filters."""
        try:
            # First get potential URLs
            map_website = self.app.map_url(url)

            # Use Claude to generate optimal selectors based on objective
            selector_prompt = f"""
            Based on this search objective, generate CSS selectors that would best target the relevant content.
            Return a JSON object with selector names and values.
            Objective: {objective}
            Example format: {{"price": ".product-price", "title": "h1.product-title"}}
            Only return valid JSON, no other text.
            """

            completion = self.client.messages.create(
                model=self.model_name,
                max_tokens=500,
                temperature=0,
                system="You are an expert at CSS selectors. Return only valid JSON.",
                messages=[{"role": "user", "content": selector_prompt}],
            )

            selectors = json.loads(completion.content[0].text)
            print(
                f"{Colors.GREEN}Generated selectors: {json.dumps(selectors, indent=2)}{Colors.RESET}"
            )

            results = []
            for target_url in map_website["links"][:3]:
                try:
                    # Extract specific content using selectors
                    extracted = self.extract_content_with_selectors(
                        target_url, selectors
                    )
                    if extracted:
                        results.append(
                            {"url": target_url, "extracted_content": extracted}
                        )
                except Exception as e:
                    print(
                        f"{Colors.YELLOW}Error processing {target_url}: {str(e)}{Colors.RESET}"
                    )
                    continue

            if results:
                return {
                    "search_type": "selective",
                    "selectors_used": selectors,
                    "results": results,
                }
            return None

        except Exception as e:
            print(f"{Colors.RED}Error in selective search: {str(e)}{Colors.RESET}")
            return None

    def batch_process(self, urls: List[str]) -> List[Dict]:
        """Process multiple URLs in parallel."""
        try:
            print(
                f"{Colors.CYAN}Processing {len(urls)} URLs in parallel...{Colors.RESET}"
            )

            # Call batch scrape endpoint
            results = self.app.batch_scrape_urls(urls, {"formats": ["markdown"]})

            # Process each result with Claude
            processed_results = []
            for result in results:
                if "markdown" in result:
                    processed = self.analyze_content(result["metadata"]["url"])
                    if processed:
                        processed_results.append(processed)

            return processed_results
        except Exception as e:
            print(f"{Colors.RED}Error during batch processing: {str(e)}{Colors.RESET}")
            return None

    def extract_content_with_selectors(
        self, url: str, selectors: Dict[str, str]
    ) -> Optional[Dict]:
        """Extract specific content using CSS selectors."""
        try:
            print(f"{Colors.CYAN}Extracting content from: {url}{Colors.RESET}")
            print(
                f"{Colors.YELLOW}Using selectors: {json.dumps(selectors, indent=2)}{Colors.RESET}"
            )

            # Call extract endpoint
            result = self.app.extract_content(url, selectors)

            if result:
                print(f"{Colors.GREEN}Content extracted successfully.{Colors.RESET}")
                return result
            return None
        except Exception as e:
            print(
                f"{Colors.RED}Error during content extraction: {str(e)}{Colors.RESET}"
            )
            return None

    def process(
        self,
        mode: Mode,
        url: str,
        objective: Optional[str] = None,
        urls: Optional[List[str]] = None,
        selectors: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict]:
        """Main processing function that handles all modes."""
        if mode == Mode.SEARCH:
            if not objective:
                raise ValueError("Objective is required for search mode")
            return self.search_content(objective, url)
        elif mode == Mode.ANALYZE:
            return self.analyze_content(url)
        elif mode == Mode.BATCH:
            if not urls:
                raise ValueError("URLs list is required for batch mode")
            return self.batch_process(urls)
        elif mode == Mode.EXTRACT:
            if not selectors:
                raise ValueError("Selectors are required for extract mode")
            return self.extract_content_with_selectors(url, selectors)


def main():
    """CLI entry point."""
    try:
        # Initialize scraper
        scraper = ClaudeScraper()

        print(f"{Colors.BLUE}Select mode:{Colors.RESET}")
        print(
            f"1. {Colors.CYAN}Search{Colors.RESET} - Find specific information across pages"
        )
        print(
            f"2. {Colors.CYAN}Analyze{Colors.RESET} - Detailed analysis of a single page"
        )
        print(
            f"3. {Colors.CYAN}Batch{Colors.RESET} - Process multiple URLs in parallel"
        )
        print(
            f"4. {Colors.CYAN}Extract{Colors.RESET} - Extract specific content using selectors"
        )
        print(f"5. {Colors.CYAN}Deep Search{Colors.RESET} - Advanced multi-mode search")

        mode_input = input(f"{Colors.BLUE}Enter mode (1-5): {Colors.RESET}")
        mode = {
            "1": Mode.SEARCH,
            "2": Mode.ANALYZE,
            "3": Mode.BATCH,
            "4": Mode.EXTRACT,
            "5": Mode.DEEP_SEARCH,
        }.get(mode_input, Mode.ANALYZE)

        if mode in [Mode.SEARCH, Mode.DEEP_SEARCH]:
            url = input(f"{Colors.BLUE}Enter the website URL: {Colors.RESET}")
            if not url.strip():
                url = "https://www.firecrawl.dev/"

            objective = input(
                f"{Colors.BLUE}Enter your search objective: {Colors.RESET}"
            )
            if not objective.strip():
                objective = "find me the pricing plans"

            if mode == Mode.DEEP_SEARCH:
                print(f"\n{Colors.BLUE}Select search type:{Colors.RESET}")
                print(
                    f"1. {Colors.CYAN}Quick{Colors.RESET} - Fast search using map endpoint"
                )
                print(f"2. {Colors.CYAN}Deep{Colors.RESET} - Detailed content analysis")
                print(
                    f"3. {Colors.CYAN}Selective{Colors.RESET} - Search with content filters"
                )

                search_type_input = input(
                    f"{Colors.BLUE}Enter search type (1-3): {Colors.RESET}"
                )
                search_type = {
                    "1": SearchType.QUICK,
                    "2": SearchType.DEEP,
                    "3": SearchType.SELECTIVE,
                }.get(search_type_input, SearchType.QUICK)

                result = scraper.search_content(objective, url, search_type)
            else:
                result = scraper.search_content(objective, url)

        elif mode == Mode.BATCH:
            print(
                f"{Colors.BLUE}Enter URLs (one per line, empty line to finish):{Colors.RESET}"
            )
            urls = []
            while True:
                url = input().strip()
                if not url:
                    break
                urls.append(url)
            if not urls:
                urls = ["https://www.firecrawl.dev/"]
            result = scraper.process(mode, url="", urls=urls)
        elif mode == Mode.EXTRACT:
            url = input(f"{Colors.BLUE}Enter the website URL: {Colors.RESET}")
            if not url.strip():
                url = "https://www.firecrawl.dev/"

            print(
                f"{Colors.BLUE}Enter selectors (one per line as 'name: selector', empty line to finish):{Colors.RESET}"
            )
            selectors = {}
            while True:
                line = input().strip()
                if not line:
                    break
                try:
                    name, selector = line.split(":", 1)
                    selectors[name.strip()] = selector.strip()
                except ValueError:
                    print(
                        f"{Colors.RED}Invalid format. Use 'name: selector'{Colors.RESET}"
                    )

            if not selectors:
                selectors = {"title": "h1", "content": "article"}
            result = scraper.process(mode, url, selectors=selectors)
        else:  # Mode.ANALYZE
            result = scraper.process(mode, url)

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
