from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
from typing import List, Dict

def search_web(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """Search DuckDuckGo and return list of results with title, url, snippet."""
    try:
        with DDGS() as ddgs:
            results = []
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                })
            return results
    except Exception as e:
        print(f"Search error: {e}")
        return []

def scrape_page(url: str, max_chars: int = 5000) -> str:
    """Scrape and return text content from a URL, truncated."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # Remove script and style elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:max_chars]
    except Exception as e:
        print(f"Scrape error for {url}: {e}")
        return ""