"""
A simple web scraper using requests and BeautifulSoup.
This script provides a function to fetch and parse HTML from a given URL.
It also includes an example usage of the function.
"""

import requests
from bs4 import BeautifulSoup
from collections import deque
import urllib.parse

def get_parsed_html(url: str):
    """
    Fetches the HTML content of a given URL and returns a BeautifulSoup object.

    Args:
        url: The URL to scrape.

    Returns:
        A BeautifulSoup object if successful, None otherwise.
    """
    try:
        # Send an HTTP GET request to the URL
        response = requests.get(url)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
        else:
            # Print an error message if the status code is not 200
            print(f"Error: Received status code {response.status_code} for URL: {url}")
            return None
    except requests.exceptions.RequestException as e:
        # Handle exceptions that may occur during the request (e.g., network issues)
        print(f"Error fetching URL {url}: {e}")
        return None

# The following block executes only when the script is run directly (not imported as a module)
if __name__ == "__main__":
    # Define the starting URL and data structures for crawling
    start_url = "http://example.com"
    visited_urls = set()
    urls_to_visit = deque([start_url])
    max_pages = 50
    pages_visited = 0

    print(f"Starting crawl from: {start_url}")

    # Main crawling loop
    while urls_to_visit and pages_visited < max_pages:
        current_url = urls_to_visit.popleft()

        if current_url in visited_urls:
            continue

        visited_urls.add(current_url)
        pages_visited += 1
        print(f"Crawling ({pages_visited}/{max_pages}): {current_url}")

        parsed_html = get_parsed_html(current_url)

        if not parsed_html:
            print(f"Failed to fetch or parse HTML from {current_url}. Skipping.")
            continue

        # Extract all unique absolute links
        anchor_tags = parsed_html.find_all('a', href=True)
        for tag in anchor_tags:
            href = tag.get('href')
            if href:
                # Join with base URL to handle relative links
                absolute_link = urllib.parse.urljoin(current_url, href)
                
                # Normalize the URL (optional, but good practice)
                # This helps in avoiding duplicate URLs due to minor differences
                # For example, http://example.com/ and http://example.com
                normalized_link = urllib.parse.urlparse(absolute_link)
                absolute_link = normalized_link._replace(fragment="").geturl() # Remove fragment

                if absolute_link not in visited_urls and absolute_link not in urls_to_visit:
                    urls_to_visit.append(absolute_link)

    print("\nCrawling finished.")
    print(f"\nVisited URLs (total: {len(visited_urls)}):")
    for url in visited_urls:
        print(url)
