
# src/retrieval/url_filter.py

from urllib.parse import urlparse
import re


# Social media and video platforms (unscrappable)
BLOCKED_DOMAINS = {
    "youtube.com",
    "youtu.be",
    "instagram.com",
    "facebook.com",
    "fb.com",
    "reddit.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "linkedin.com",
    "pinterest.com",
    "tumblr.com",
    "snapchat.com",
    "whatsapp.com",
    "quora.com",
    "discord.com",
    "https://encyclopedia.ushmm.org",
    "twitch.tv",
    "vimeo.com",
}

# E-commerce and booking sites (low factual value)
COMMERCE_DOMAINS = {
    "amazon.",
    "flipkart.com",
    "ebay.",
    "alibaba.com",
    "shopify.com",
    "etsy.com",
    "booking.com",
    "hotels.com",
    "airbnb.com",
    "tripadvisor",
    "expedia.com",
    "makemytrip.com",
    "goibibo.com",
    "cleartrip.com"
}

# Classified ads and directories (low quality)
CLASSIFIED_DOMAINS = {
    "justdial.com",
    "sulekha.com",
    "quikr.com",
    "olx.",
    "craigslist.org",
    "gumtree.com",
    "yelp.com",
    "yellowpages.com"
}

# Government tender/procurement sites (usually irrelevant)
TENDER_DOMAINS = {
    "etenders.gov",
    "eprocure.",
    "tender",
    "gem.gov.in"
}


def is_scrapable(url: str) -> bool:
    """
    Check if URL should be scraped.
    Returns False for social media, e-commerce, etc.
    """
    if not url or not isinstance(url, str):
        return False
    
    url_lower = url.lower()
    domain = urlparse(url_lower).netloc
    
    # Block social media
    if any(blocked in domain for blocked in BLOCKED_DOMAINS):
        return False
    
    # Block e-commerce
    if any(commerce in url_lower for commerce in COMMERCE_DOMAINS):
        return False
    
    # Block classifieds
    if any(classified in url_lower for classified in CLASSIFIED_DOMAINS):
        return False
    
    # Block tender sites
    if any(tender in url_lower for tender in TENDER_DOMAINS):
        return False
    
    # Block PDFs (hard to extract clean text)
    if url_lower.endswith('.pdf'):
        return False
    
    # Block image/video files
    if any(url_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.mov']):
        return False
    
    # Block URLs with too many query parameters (usually dynamic/generated)
    if url_lower.count('?') > 0 and url_lower.count('&') > 3:
        return False
    
    return True


def is_high_authority(url: str) -> bool:
    """
    Check if URL is from a high-authority source.
    Used for prioritization, not filtering.
    """
    url_lower = url.lower()
    
    high_authority = [
        'wikipedia.org',
        'britannica.com',
        '.gov',
        '.edu',
        'bbc.com',
        'reuters.com',
        'apnews.com',
        'theguardian.com',
        'nytimes.com',
        'washingtonpost.com',
        'thehindu.com',
        'hindustantimes.com',
        'indiatoday.in',
        'indianexpress.com',
        'timesofindia.com',
        'snopes.com',
        'factcheck.org',
        'politifact.com',
        'fullfact.org',
        'who.int',
        'cdc.gov',
        'nih.gov',
        'nature.com',
        'sciencemag.org',
        'pubmed.gov'
    ]
    
    return any(auth in url_lower for auth in high_authority)


def extract_domain_name(url: str) -> str:
    """Extract clean domain name for display"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        # Take first part before TLD
        name = domain.split('.')[0]
        return name.capitalize()
    except:
        return "Web Source"