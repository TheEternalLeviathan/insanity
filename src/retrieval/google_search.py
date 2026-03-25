import os
import requests
import json
from dotenv import load_dotenv
from typing import List

load_dotenv()

class GoogleSearchClient:
    """
    Serper.dev Google Search API client.
    A high-performance alternative to Google Custom Search.
    """
    
    def __init__(self):
        # Use your Serper API Key from .env
        self.api_key = os.getenv("SERPER_API_KEY")
    
    def search(self, query: str, num_results: int = 10) -> List[str]:
        """
        Search Google via Serper and return organic URLs.
        """
        if not self.api_key:
            print("⚠️ Serper API key not configured (SERPER_API_KEY)")
            return []
        
        url = "https://google.serper.dev/search"
        
        # Serper uses a POST request with a JSON payload
        payload = json.dumps({
            "q": query,
            "num": min(num_results, 20)  # Serper allows more than 10
        })
        
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            # Note: Changed from requests.get to requests.post
            response = requests.post(url, headers=headers, data=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Serper returns organic results in the 'organic' list
            results = data.get("organic", [])
            
            if not results:
                print(f"   ⚠️ No organic results from Serper")
                return []
            
            # Extract URLs from the 'link' field
            urls = [item["link"] for item in results if "link" in item]
            
            return urls
            
        except requests.exceptions.Timeout:
            print(f"   ⚠️ Serper Search timeout")
            return []
        except requests.exceptions.HTTPError as e:
            # Handles 403 (Invalid Key) or 429 (Rate Limit) specifically
            print(f"   ⚠️ Serper API error: {e}")
            return []
        except Exception as e:
            print(f"   ⚠️ Serper search failed: {str(e)[:50]}")
            return []