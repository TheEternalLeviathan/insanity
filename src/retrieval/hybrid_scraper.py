

# src/retrieval/hybrid_scraper.py

from firecrawl import FirecrawlApp
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urlparse
from dotenv import load_dotenv
load_dotenv()

class HybridScraper:
    """
    Intelligent scraper that uses:
    1. Firecrawl (premium, clean) when available
    2. WebScraper (free, reliable) as fallback
    """
    
    def __init__(self):
        # Try to initialize Firecrawl
        try:
            api_key = os.getenv("FIRECRAWL_API_KEY")
            if api_key:
                self.firecrawl = FirecrawlApp(api_key=api_key)
                self.use_firecrawl = True
                print("✅ Hybrid Scraper: Firecrawl + WebScraper fallback")
            else:
                self.firecrawl = None
                self.use_firecrawl = False
                print("✅ Hybrid Scraper: WebScraper only (no Firecrawl key)")
        except Exception as e:
            self.firecrawl = None
            self.use_firecrawl = False
            print(f"⚠️ Firecrawl init failed: {e}")
            print("✅ Hybrid Scraper: WebScraper only")
        
        # WebScraper headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        # Track Firecrawl failures for adaptive switching
        self.firecrawl_failures = 0
        self.firecrawl_max_failures = 3
    
    def _extract_title_from_url(self, url: str) -> str:
        """Extract a readable source name from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            
            # Remove www. prefix
            domain = domain.replace('www.', '')
            
            # Remove .com, .org, etc
            domain = domain.split('.')[0]
            
            # Capitalize first letter
            return domain.capitalize()
        except:
            return "Web Source"
    
    def scrape(self, urls, max_pages=2):
        """
        Scrape URLs using intelligent switching:
        - Try Firecrawl first (if available and not failing)
        - Fall back to WebScraper on failure
        - Auto-switch to WebScraper if Firecrawl keeps failing
        """
        results = []
        
        print(f"📄 Scraping {min(max_pages, len(urls))} URLs...")
        
        for i, url in enumerate(urls[:max_pages], 1):
            print(f"   {i}. {url[:60]}...")
            
            # Try Firecrawl first (if available and not repeatedly failing)
            if self.use_firecrawl and self.firecrawl_failures < self.firecrawl_max_failures:
                result = self._try_firecrawl(url)
                if result:
                    results.append(result)
                    self.firecrawl_failures = max(0, self.firecrawl_failures - 1)
                    continue
                else:
                    self.firecrawl_failures += 1
                    print(f"      ⚠️ Firecrawl failed ({self.firecrawl_failures}/{self.firecrawl_max_failures}), trying WebScraper...")
            
            # Fallback to WebScraper
            result = self._try_webscraper(url)
            if result:
                results.append(result)
        
        print(f"✅ Successfully scraped {len(results)} pages")
        
        # Reset failure count if we got good results
        if len(results) > 0:
            self.firecrawl_failures = 0
        
        return results
    
    def _try_firecrawl(self, url):
        """Try scraping with Firecrawl (premium quality)"""
        try:
            doc = self.firecrawl.scrape(
                url,
                formats=["markdown"],
                only_main_content=True
            )
            
            content = getattr(doc, "markdown", "") or getattr(doc, "content", "")
            title = getattr(doc, "title", None) or self._extract_title_from_url(url)
            
            if content and len(content) > 300:
                print(f"      ✅ Firecrawl: {len(content)} chars")
                return {
                    "url": url,
                    "content": content[:6000],
                    "title": title,
                    "source": "firecrawl"
                }
            else:
                return None
                
        except Exception as e:
            error_msg = str(e)
            
            if "Payment Required" in error_msg or "Insufficient credits" in error_msg:
                print(f"      ❌ Firecrawl: Out of credits")
                self.use_firecrawl = False
            elif "429" in error_msg or "rate limit" in error_msg.lower():
                print(f"      ❌ Firecrawl: Rate limited")
            else:
                print(f"      ❌ Firecrawl: {str(e)[:50]}")
            
            return None
    
    def _try_webscraper(self, url):
        """Try scraping with WebScraper (free, reliable)"""
        try:
            # Make request
            response = requests.get(url, headers=self.headers, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else self._extract_title_from_url(url)
            
            # Clean title (remove site name suffixes)
            if ' - ' in title:
                title = title.split(' - ')[0]
            if ' | ' in title:
                title = title.split(' | ')[0]
            
            # Limit title length
            if len(title) > 80:
                title = title[:77] + "..."
            
            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
                element.decompose()
            
            # Try to get main content
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.body
            
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
            else:
                text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit content
            content = text[:6000]
            
            if len(content) > 300:
                print(f"      ✅ WebScraper: {len(content)} chars")
                return {
                    "url": url,
                    "content": content,
                    "title": title,
                    "source": "webscraper"
                }
            else:
                print(f"      ⚠️ Content too short: {len(content)} chars")
                return None
                
        except requests.exceptions.Timeout:
            print(f"      ⚠️ WebScraper: Timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"      ❌ WebScraper: {str(e)[:50]}")
            return None
        except Exception as e:
            print(f"      ❌ WebScraper: {str(e)[:50]}")
            return None
    
    def get_stats(self):
        """Get scraper statistics"""
        return {
            "firecrawl_enabled": self.use_firecrawl,
            "firecrawl_failures": self.firecrawl_failures,
            "mode": "hybrid" if self.use_firecrawl else "webscraper_only"
        }