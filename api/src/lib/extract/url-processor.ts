import { MapDocument, URLTrace } from "../../controllers/v1/types";
import { getMapResults } from "../../controllers/v1/map";
import { PlanType } from "../../types";
import { removeDuplicateUrls } from "../validateUrl";
import { isUrlBlocked } from "../../scraper/WebScraper/utils/blocklist";
import { generateBasicCompletion } from "../LLM-extraction";
import { buildRefrasedPrompt } from "./build-prompts";
import { logger } from "../logger";
import { rerankLinks } from "./reranker";
import { extractConfig } from "./config";

interface ProcessUrlOptions {
  url: string;
  prompt?: string;
  teamId: string;
  plan: PlanType;
  allowExternalLinks?: boolean;
  origin?: string;
  limit?: number;
  includeSubdomains?: boolean;
}

export async function processUrl(options: ProcessUrlOptions, urlTraces: URLTrace[]): Promise<string[]> {
  const trace: URLTrace = {
    url: options.url,
    status: 'mapped',
    timing: {
      discoveredAt: new Date().toISOString(),
    },
  };
  urlTraces.push(trace);

  if (!options.url.includes("/*") && !options.allowExternalLinks) {
    if (!isUrlBlocked(options.url)) {
      trace.usedInCompletion = true;
      return [options.url];
    }
    trace.status = 'error';
    trace.error = 'URL is blocked';
    trace.usedInCompletion = false;
    return [];
  }

  const baseUrl = options.url.replace("/*", "");
  let urlWithoutWww = baseUrl.replace("www.", "");

  let rephrasedPrompt = options.prompt;
  if (options.prompt) {
    rephrasedPrompt = await generateBasicCompletion(
      buildRefrasedPrompt(options.prompt, baseUrl)
    ) ?? options.prompt;
  }

  try {
    const mapResults = await getMapResults({
      url: baseUrl,
      search: rephrasedPrompt,
      teamId: options.teamId,
      plan: options.plan,
      allowExternalLinks: options.allowExternalLinks,
      origin: options.origin,
      limit: options.limit,
      ignoreSitemap: false,
      includeMetadata: true,
      includeSubdomains: options.includeSubdomains,
    });

    let mappedLinks = mapResults.mapResults as MapDocument[];
    let allUrls = [...mappedLinks.map((m) => m.url), ...mapResults.links];
    let uniqueUrls = removeDuplicateUrls(allUrls);

    // Track all discovered URLs
    uniqueUrls.forEach(discoveredUrl => {
      if (!urlTraces.some(t => t.url === discoveredUrl)) {
        urlTraces.push({
          url: discoveredUrl,
          status: 'mapped',
          timing: {
            discoveredAt: new Date().toISOString(),
          },
          usedInCompletion: false,
        });
      }
    });

    // retry if only one url is returned
    if (uniqueUrls.length <= 1)  {
      const retryMapResults = await getMapResults({
        url: baseUrl,
        teamId: options.teamId,
        plan: options.plan,
        allowExternalLinks: options.allowExternalLinks,
        origin: options.origin,
        limit: options.limit,
        ignoreSitemap: false,
        includeMetadata: true,
        includeSubdomains: options.includeSubdomains,
      });
  
      mappedLinks = retryMapResults.mapResults as MapDocument[];
      allUrls = [...mappedLinks.map((m) => m.url), ...mapResults.links];
      uniqueUrls = removeDuplicateUrls(allUrls);

      // Track all discovered URLs
      uniqueUrls.forEach(discoveredUrl => {
        if (!urlTraces.some(t => t.url === discoveredUrl)) {
          urlTraces.push({
            url: discoveredUrl,
            status: 'mapped',
            warning: 'Broader search. Not limiting map results to prompt.',
            timing: {
              discoveredAt: new Date().toISOString(),
            },
            usedInCompletion: false,
          });
        }
      });
    }

    // Track all discovered URLs
    uniqueUrls.forEach(discoveredUrl => {
      if (!urlTraces.some(t => t.url === discoveredUrl)) {
        urlTraces.push({
          url: discoveredUrl,
          status: 'mapped',
          timing: {
            discoveredAt: new Date().toISOString(),
          },
          usedInCompletion: false,
        });
      }
    });

    const existingUrls = new Set(mappedLinks.map((m) => m.url));
    const newUrls = uniqueUrls.filter((url) => !existingUrls.has(url));

    mappedLinks = [
      ...mappedLinks,
      ...newUrls.map((url) => ({ url, title: "", description: "" })),
    ];

    if (mappedLinks.length === 0) {
      mappedLinks = [{ url: baseUrl, title: "", description: "" }];
    }

    // Limit initial set of links (1000)
    mappedLinks = mappedLinks.slice(0, extractConfig.MAX_INITIAL_RANKING_LIMIT);

    // Perform reranking if prompt is provided
    if (options.prompt) {
      const searchQuery = options.allowExternalLinks
        ? `${options.prompt} ${urlWithoutWww}`
        : `${options.prompt} site:${urlWithoutWww}`;

      mappedLinks = await rerankLinks(mappedLinks, searchQuery, urlTraces);
    }

    return mappedLinks.map(x => x.url);
  } catch (error) {
    trace.status = 'error';
    trace.error = error.message;
    trace.usedInCompletion = false;
    return [];
  }
} 