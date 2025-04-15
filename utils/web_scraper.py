import requests
from bs4 import BeautifulSoup
import trafilatura
import time
import random
from urllib.parse import urlparse

def scrape_website(url):
    """
    Scrape a website and return its content in a format suitable for classification.
    
    Args:
        url (str): The URL of the website to scrape
        
    Returns:
        str: The extracted text content of the website
    
    Raises:
        Exception: If the website cannot be scraped
    """
    try:
        # First try with trafilatura for cleaner content extraction
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            content = trafilatura.extract(downloaded)
            if content and len(content) > 100:  # Ensure we have meaningful content
                return content
        
        # Fallback to requests + BeautifulSoup if trafilatura doesn't get enough content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "noscript", "iframe", "head"]):
            script.extract()
        
        # Get text content
        text = soup.get_text(separator=' ')
        
        # Clean the text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Try to get meta description
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag and meta_tag.get("content"):
            meta_desc = meta_tag.get("content").strip()
        
        # Try to get page title
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.text.strip()
        
        # Get domain name for additional context
        domain = urlparse(url).netloc
        
        # Assemble the context
        context = f"URL: {url}\nDomain: {domain}\nTitle: {title}\nDescription: {meta_desc}\n\nContent:\n{text}"
        
        return context
        
    except Exception as e:
        # Add a slight delay before raising to avoid overwhelming servers
        time.sleep(random.uniform(1, 3))
        raise Exception(f"Failed to scrape {url}: {str(e)}")
