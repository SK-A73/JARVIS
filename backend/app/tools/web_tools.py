"""
Internet & Technical Documentation Tools
Enables JARVIS to research programming libraries, APIs, and official developer docs safely.
"""
import re
import httpx
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from backend.app.core.security import sanitize_secrets

async def fetch_web_documentation(url: str, max_chars: int = 10000) -> Dict[str, Any]:
    """Fetches and extracts clean markdown/text documentation from authoritative web sources."""
    headers = {
        "User-Agent": "JARVIS-Developer-Assistant/1.0 (Autonomous Technical Agent; +https://jarvis.ai)"
    }
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Strip scripts, styles, navigation, headers, footers
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        if len(clean_text) > max_chars:
            clean_text = clean_text[:max_chars] + "\n...[Content truncated for length]..."

        return {
            "success": True,
            "url": url,
            "title": soup.title.string if soup.title else url,
            "content": sanitize_secrets(clean_text)
        }
    except Exception as e:
        return {
            "success": False,
            "url": url,
            "error": sanitize_secrets(f"Failed to fetch documentation: {str(e)}")
        }

async def web_search(query: str) -> Dict[str, Any]:
    """Simulates or invokes authoritative technical searches (Python docs, MDN, GitHub)."""
    # Return structured search format
    return {
        "query": query,
        "results": [
            {
                "title": f"Official Documentation for: {query}",
                "snippet": f"Developer reference, API parameters, and syntax specifications for {query}.",
                "url": f"https://docs.python.org/3/search.html?q={query.replace(' ', '+')}"
            }
        ]
    }
