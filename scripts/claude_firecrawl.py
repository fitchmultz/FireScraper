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


def find_relevant_page_via_map(objective: str, url: str) -> list:
    """Find pages that most likely contain the objective."""
    try:
        print(f"{Colors.CYAN}Understood. The objective is: {objective}{Colors.RESET}")
        print(f"{Colors.CYAN}Initiating search on the website: {url}{Colors.RESET}")

        map_prompt = f"""
        The map function generates a list of URLs from a website and it accepts a search parameter. Based on the objective of: {objective}, come up with a 1-2 word search parameter that will help us find the information we need. Only respond with 1-2 words nothing else.
        """

        print(
            f"{Colors.YELLOW}Analyzing objective to determine optimal search parameter...{Colors.RESET}"
        )
        completion = client.messages.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
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
        map_website = app.map_url(url, params={"search": map_search_parameter})
        print(f"{Colors.GREEN}Website mapping completed successfully.{Colors.RESET}")
        print(
            f"{Colors.GREEN}Located {len(map_website['links'])} relevant links.{Colors.RESET}"
        )

        return map_website["links"]
    except Exception as e:
        print(f"{Colors.RED}Error during page identification: {str(e)}{Colors.RESET}")
        return None


def find_objective_in_top_pages(map_website: list, objective: str) -> dict:
    """Scrape top pages and check if objective is met."""
    try:
        # Get top 2 links from the map result
        top_links = map_website[:2]
        print(
            f"{Colors.CYAN}Proceeding to analyze top {len(top_links)} links: {top_links}{Colors.RESET}"
        )

        # Scrape the pages in batch
        print(
            f"{Colors.YELLOW}Starting batch scrape of URLs: {top_links}{Colors.RESET}"
        )
        try:
            # Try scraping one URL at a time instead of batch
            all_results = []
            for url in top_links:
                print(f"{Colors.YELLOW}Scraping URL: {url}{Colors.RESET}")
                try:
                    print(
                        f"{Colors.YELLOW}Making API request to Firecrawl...{Colors.RESET}"
                    )
                    # Add timeout and debug info
                    print(f"{Colors.YELLOW}URL being requested: {url}{Colors.RESET}")
                    print(
                        f"{Colors.YELLOW}API URL being used: {app.api_url}{Colors.RESET}"
                    )
                    result = app.scrape_url(
                        url, {"formats": ["markdown"], "timeout": 30000}
                    )
                    print(
                        f"{Colors.YELLOW}API response received. Status: {result.get('status', 'unknown')}{Colors.RESET}"
                    )
                    all_results.append({"url": url, "markdown": result["markdown"]})
                    print(f"{Colors.GREEN}Successfully scraped: {url}{Colors.RESET}")
                except Exception as e:
                    print(f"{Colors.RED}Error scraping {url}: {str(e)}{Colors.RESET}")
                    print(f"{Colors.RED}Error type: {type(e)}{Colors.RESET}")
                    print(f"{Colors.RED}Full error details: {repr(e)}{Colors.RESET}")
                    continue

            if not all_results:
                print(f"{Colors.RED}Failed to scrape any URLs{Colors.RESET}")
                return None

            batch_scrape_result = {"data": all_results}
            print(f"{Colors.GREEN}All pages scraped successfully.{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}Error during scraping: {str(e)}{Colors.RESET}")
            return None

        print(f"{Colors.YELLOW}Processing batch results...{Colors.RESET}")

        for scrape_result in batch_scrape_result["data"]:
            check_prompt = f"""
            Given the following scraped content and objective, determine if the objective is met.
            If it is, extract the relevant information in a simple and concise JSON format. Use only the necessary fields and avoid nested structures if possible.
            If the objective is not met with confidence, respond with 'Objective not met'.

            Objective: {objective}
            Scraped content: {scrape_result['markdown']}

            Remember:
            1. Only return JSON if you are confident the objective is fully met.
            2. Keep the JSON structure as simple and flat as possible.
            3. Do not include any explanations or markdown formatting in your response.
            """

            completion = client.messages.create(
                model=MODEL_NAME,
                max_tokens=1000,
                temperature=0,
                system="You are an expert web crawler. Respond with the relevant information in JSON format.",
                messages=[{"role": "user", "content": check_prompt}],
            )

            result = completion.content[0].text

            if result != "Objective not met":
                print(
                    f"{Colors.GREEN}Objective potentially fulfilled. Relevant information identified.{Colors.RESET}"
                )
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    print(
                        f"{Colors.RED}Error parsing response. Proceeding to next page...{Colors.RESET}"
                    )
            else:
                print(
                    f"{Colors.YELLOW}Objective not met on this page. Proceeding to next link...{Colors.RESET}"
                )

        print(
            f"{Colors.RED}All available pages analyzed. Objective not fulfilled.{Colors.RESET}"
        )
        return None

    except Exception as e:
        print(f"{Colors.RED}Error during page analysis: {str(e)}{Colors.RESET}")
        return None


def main():
    """CLI entry point for the crawler."""
    # Get user input
    url = input(f"{Colors.BLUE}Enter the website to crawl: {Colors.RESET}")
    if not url.strip():
        url = "https://www.firecrawl.dev/"

    objective = input(f"{Colors.BLUE}Enter your objective: {Colors.RESET}")
    if not objective.strip():
        objective = "find me the pricing plans"

    print(f"{Colors.YELLOW}Initiating web crawling process...{Colors.RESET}")

    # Find the relevant pages
    map_website = find_relevant_page_via_map(objective, url)

    if map_website:
        print(
            f"{Colors.GREEN}Relevant pages identified. Proceeding with detailed analysis...{Colors.RESET}"
        )
        result = find_objective_in_top_pages(map_website, objective)

        if result:
            print(
                f"{Colors.GREEN}Objective successfully fulfilled. Extracted information:{Colors.RESET}"
            )
            print(f"{Colors.MAGENTA}{json.dumps(result, indent=2)}{Colors.RESET}")
        else:
            print(
                f"{Colors.RED}Unable to fulfill the objective with the available content.{Colors.RESET}"
            )
    else:
        print(
            f"{Colors.RED}No relevant pages identified. Consider refining the search.{Colors.RESET}"
        )


if __name__ == "__main__":
    main()
