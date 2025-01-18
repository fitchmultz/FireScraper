#!/usr/bin/env python3

import json
import sys
import traceback
from typing import Optional

from modules.claude_scraper import ClaudeScraper, Mode, SearchType
from modules.cli import parse_args
from modules.crawl import CrawlConfig, crawl_and_save
from modules.utils import format_error, format_info, format_warning


def main():
    args = parse_args()

    # Set up verbose mode globally
    if args.verbose:
        print(format_info("Verbose mode enabled"))

    try:
        if args.command == "crawl":
            config = CrawlConfig(
                url=args.url,
                max_depth=args.max_depth,
                max_pages=args.max_pages,
                allow_external=args.allow_external,
                allow_subdomains=args.allow_subdomains,
                languages=set(args.languages),
                exclude_patterns=args.exclude_patterns,
                include_patterns=args.include_patterns,
                output_dir=args.output_dir,
                save_raw_html=args.save_html,
                check_interval=args.check_interval,
                timeout=args.timeout,
            )
            config.display_config()
            crawl_and_save(config)
        else:
            scraper = ClaudeScraper()
            if args.command == "search":
                search_type = SearchType[args.type.upper()]
                result = scraper.process(
                    Mode.SEARCH,
                    args.url,
                    objective=args.objective,
                )
            elif args.command == "analyze":
                result = scraper.process(Mode.ANALYZE, args.url)
            elif args.command == "batch":
                result = scraper.process(Mode.BATCH, urls=args.urls)
            elif args.command == "extract":
                selectors = json.loads(args.selectors)
                result = scraper.process(
                    Mode.EXTRACT,
                    args.url,
                    selectors=selectors,
                )

            if args.verbose:
                print(json.dumps(result, indent=2))
            else:
                print(result)

    except KeyboardInterrupt:
        print(f"\n{format_warning('Operation cancelled by user')}")
        sys.exit(1)
    except Exception as e:
        print(format_error(str(e)))
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
