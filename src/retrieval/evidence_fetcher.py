
# src/retrieval/evidence_fetcher.py

from src.retrieval.query_generator import QueryGenerator
from src.retrieval.google_search import GoogleSearchClient
from src.retrieval.hybrid_scraper import HybridScraper
from src.retrieval.url_filter import is_scrapable
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class EvidenceFetcher:
    def __init__(self):
        self.qg = QueryGenerator()
        self.search = GoogleSearchClient()
        self.scraper = HybridScraper()

    def fetch(self, claim: str, max_evidence: int = 10):
        """Fetch evidence with parallel scraping"""
        evidence = []
        seen = set()

        # Generate queries
        queries = self.qg.generate(claim)
        
        # Collect all URLs from all queries first
        all_urls = []
        for query in queries:
            urls = self.search.search(query, num_results=8)
            for url in urls:
                if url not in seen and is_scrapable(url):
                    all_urls.append(url)
                    seen.add(url)
                    
                    if len(all_urls) >= 10:  # Max 10 URLs total
                        break
            
            if len(all_urls) >= 10:
                break
        
        # ⚡ PARALLEL SCRAPING (huge speedup!)
        print(f"\n⚡ Scraping {len(all_urls)} URLs in parallel...")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all scraping tasks
            future_to_url = {
                executor.submit(self._scrape_single, url): url 
                for url in all_urls[:6]  # Scrape top 6 URLs
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_url):
                if len(evidence) >= max_evidence:
                    break
                
                try:
                    result = future.result(timeout=15)  # 15s timeout per URL
                    if result:
                        evidence.append(result)
                except Exception as e:
                    url = future_to_url[future]
                    print(f"   ⚠️ Failed: {url[:60]} - {e}")
        
        elapsed = time.time() - start_time
        print(f"   ✅ Scraped {len(evidence)} docs in {elapsed:.1f}s (parallel)\n")
        
        return evidence[:max_evidence]
    
    def _scrape_single(self, url: str):
        """Scrape a single URL (called in parallel)"""
        results = self.scraper.scrape([url], max_pages=1)
        return results[0] if results else None