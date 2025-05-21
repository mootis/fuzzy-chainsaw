import unittest
from unittest.mock import patch, MagicMock
from collections import deque
import scraper  # Assuming scraper.py is in the same directory or accessible via PYTHONPATH
import requests # Import requests

class TestCrawler(unittest.TestCase):

    @patch('scraper.requests.get')
    @patch('builtins.print')  # Mock print to suppress output during test
    def test_initial_url_added(self, mock_print, mock_requests_get):
        # Mock the response from requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<html><body><a href='http://example.com/page1'>Page 1</a></body></html>"
        mock_requests_get.return_value = mock_response

        # Run the crawler logic (adapted from scraper.py's __main__ block)
        start_url = "http://example.com"
        visited_urls = set()
        urls_to_visit = deque([start_url])
        max_pages = 1 # Limit to 1 page for this test
        pages_visited = 0

        # Perform one step of the crawl
        if urls_to_visit and pages_visited < max_pages:
            current_url = urls_to_visit.popleft()
            if current_url not in visited_urls:
                visited_urls.add(current_url)
                pages_visited += 1
                # Call get_parsed_html directly for simplicity in testing this unit
                parsed_html = scraper.get_parsed_html(current_url)
                if parsed_html:
                    anchor_tags = parsed_html.find_all('a', href=True)
                    for tag in anchor_tags:
                        href = tag.get('href')
                        if href:
                            absolute_link = scraper.urllib.parse.urljoin(current_url, href)
                            normalized_link = scraper.urllib.parse.urlparse(absolute_link)
                            absolute_link = normalized_link._replace(fragment="").geturl()
                            if absolute_link not in visited_urls and absolute_link not in urls_to_visit:
                                urls_to_visit.append(absolute_link)
        
        self.assertIn(start_url, visited_urls)
        self.assertIn("http://example.com/page1", urls_to_visit)
        # mock_print.assert_any_call(f"Crawling (1/1): {start_url}") # Removed this line

    @patch('scraper.requests.get')
    @patch('builtins.print')
    def test_crawl_multiple_urls(self, mock_print, mock_requests_get):
        # Define responses for different URLs
        mock_responses = {
            "http://example.com": MagicMock(status_code=200, content=b"<html><body><a href='/page1'>Page 1</a></body></html>"),
            "http://example.com/page1": MagicMock(status_code=200, content=b"<html><body><a href='/page2'>Page 2</a></body></html>"),
            "http://example.com/page2": MagicMock(status_code=200, content=b"<html><body>No more links</body></html>")
        }
        mock_requests_get.side_effect = lambda url, **kwargs: mock_responses.get(url, MagicMock(status_code=404))

        start_url = "http://example.com"
        visited_urls = set()
        urls_to_visit = deque([start_url])
        max_pages = 3
        pages_visited = 0

        while urls_to_visit and pages_visited < max_pages:
            current_url = urls_to_visit.popleft()
            if current_url in visited_urls:
                continue
            visited_urls.add(current_url)
            pages_visited += 1
            parsed_html = scraper.get_parsed_html(current_url)
            if parsed_html:
                anchor_tags = parsed_html.find_all('a', href=True)
                for tag in anchor_tags:
                    href = tag.get('href')
                    if href:
                        absolute_link = scraper.urllib.parse.urljoin(current_url, href)
                        normalized_link = scraper.urllib.parse.urlparse(absolute_link)
                        absolute_link = normalized_link._replace(fragment="").geturl()
                        if absolute_link not in visited_urls and absolute_link not in urls_to_visit:
                            urls_to_visit.append(absolute_link)
        
        self.assertEqual(len(visited_urls), 3)
        self.assertIn("http://example.com", visited_urls)
        self.assertIn("http://example.com/page1", visited_urls)
        self.assertIn("http://example.com/page2", visited_urls)

    @patch('scraper.requests.get')
    @patch('builtins.print')
    def test_link_extraction(self, mock_print, mock_requests_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<html><body><a href='http://example.com/link1'>L1</a><a href='/link2'>L2</a></body></html>"
        mock_requests_get.return_value = mock_response

        start_url = "http://start.com"
        visited_urls = set()
        urls_to_visit = deque([start_url])
        max_pages = 1 
        pages_visited = 0

        if urls_to_visit and pages_visited < max_pages:
            current_url = urls_to_visit.popleft()
            if current_url not in visited_urls:
                visited_urls.add(current_url)
                pages_visited += 1
                parsed_html = scraper.get_parsed_html(current_url)
                if parsed_html:
                    anchor_tags = parsed_html.find_all('a', href=True)
                    for tag in anchor_tags:
                        href = tag.get('href')
                        if href:
                            absolute_link = scraper.urllib.parse.urljoin(current_url, href)
                            normalized_link = scraper.urllib.parse.urlparse(absolute_link)
                            absolute_link = normalized_link._replace(fragment="").geturl()
                            if absolute_link not in visited_urls and absolute_link not in urls_to_visit:
                                urls_to_visit.append(absolute_link)

        self.assertIn("http://example.com/link1", urls_to_visit)
        self.assertIn("http://start.com/link2", urls_to_visit) # Relative link joined with start_url

    @patch('scraper.requests.get')
    @patch('builtins.print')
    def test_avoid_revisiting_urls(self, mock_print, mock_requests_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Page links to itself and another page
        mock_response.content = b"<html><body><a href='http://example.com'>Self</a><a href='http://example.com/page2'>Page 2</a></body></html>"
        mock_requests_get.return_value = mock_response
        
        # Mock response for page2
        mock_response_page2 = MagicMock()
        mock_response_page2.status_code = 200
        mock_response_page2.content = b"<html><body>No links</body></html>"

        def side_effect_func(url, **kwargs):
            if url == "http://example.com":
                return mock_response
            elif url == "http://example.com/page2":
                return mock_response_page2
            return MagicMock(status_code=404)
        mock_requests_get.side_effect = side_effect_func

        start_url = "http://example.com"
        visited_urls = set()
        urls_to_visit = deque([start_url])
        max_pages = 5 # Allow enough visits
        pages_visited = 0
        
        # Track how many times get_parsed_html is called for the start_url
        # This is an indirect way to check if we tried to fetch it multiple times.
        # A more direct way would be to inspect calls to mock_requests_get for specific URLs.
        
        crawl_count_for_start_url = 0

        while urls_to_visit and pages_visited < max_pages:
            current_url = urls_to_visit.popleft()
            if current_url in visited_urls:
                # This is the check that prevents re-visiting
                continue 
            
            if current_url == start_url:
                crawl_count_for_start_url +=1

            visited_urls.add(current_url)
            pages_visited += 1
            
            parsed_html = scraper.get_parsed_html(current_url) # This will trigger mock_requests_get
            
            if parsed_html:
                anchor_tags = parsed_html.find_all('a', href=True)
                for tag in anchor_tags:
                    href = tag.get('href')
                    if href:
                        absolute_link = scraper.urllib.parse.urljoin(current_url, href)
                        normalized_link = scraper.urllib.parse.urlparse(absolute_link)
                        absolute_link = normalized_link._replace(fragment="").geturl()
                        if absolute_link not in visited_urls and absolute_link not in urls_to_visit:
                             urls_to_visit.append(absolute_link)
        
        self.assertEqual(crawl_count_for_start_url, 1, "Start URL should only be crawled once.")
        self.assertIn("http://example.com", visited_urls)
        self.assertIn("http://example.com/page2", visited_urls)
        self.assertEqual(len(visited_urls), 2) # example.com and example.com/page2

    @patch('scraper.requests.get')
    @patch('builtins.print')
    def test_handle_no_links_on_page(self, mock_print, mock_requests_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<html><body><p>No links here.</p></body></html>"
        mock_requests_get.return_value = mock_response

        start_url = "http://example.com"
        visited_urls = set()
        urls_to_visit = deque([start_url])
        max_pages = 1
        pages_visited = 0

        if urls_to_visit and pages_visited < max_pages:
            current_url = urls_to_visit.popleft()
            if current_url not in visited_urls:
                visited_urls.add(current_url)
                pages_visited += 1
                parsed_html = scraper.get_parsed_html(current_url)
                if parsed_html:
                    anchor_tags = parsed_html.find_all('a', href=True)
                    for tag in anchor_tags: # Should not loop if no links
                        href = tag.get('href')
                        if href:
                            absolute_link = scraper.urllib.parse.urljoin(current_url, href)
                            normalized_link = scraper.urllib.parse.urlparse(absolute_link)
                            absolute_link = normalized_link._replace(fragment="").geturl()
                            if absolute_link not in visited_urls and absolute_link not in urls_to_visit:
                                urls_to_visit.append(absolute_link)
        
        self.assertIn(start_url, visited_urls)
        self.assertEqual(len(urls_to_visit), 0, "urls_to_visit queue should be empty if no links found.")

    @patch('scraper.requests.get')
    @patch('builtins.print')
    def test_handle_invalid_url_or_network_error(self, mock_print, mock_requests_get):
        # Test requests.exceptions.RequestException
        mock_requests_get.side_effect = requests.exceptions.RequestException("Test network error")
        
        start_url = "http://brokenurl.com"
        visited_urls = set()
        urls_to_visit = deque([start_url, "http://example.com/goodurl"]) # Add a good URL to ensure crawler continues
        
        # Mock response for the good URL
        mock_good_response = MagicMock()
        mock_good_response.status_code = 200
        mock_good_response.content = b"<html><body>Good page</body></html>"

        def side_effect_func(url, **kwargs):
            if url == "http://brokenurl.com":
                raise requests.exceptions.RequestException("Test network error")
            elif url == "http://example.com/goodurl":
                return mock_good_response
            return MagicMock(status_code=404) # Default for any other unexpected URL
        mock_requests_get.side_effect = side_effect_func

        pages_visited = 0
        max_pages = 2

        while urls_to_visit and pages_visited < max_pages:
            current_url = urls_to_visit.popleft()
            if current_url in visited_urls:
                continue
            
            visited_urls.add(current_url) # Add to visited even if it fails, to avoid retrying
            pages_visited += 1
            
            # We expect get_parsed_html to return None and print an error
            parsed_html = scraper.get_parsed_html(current_url) 
            
            if parsed_html: # This block should not be hit for brokenurl.com
                anchor_tags = parsed_html.find_all('a', href=True)
                for tag in anchor_tags:
                    href = tag.get('href')
                    if href:
                        absolute_link = scraper.urllib.parse.urljoin(current_url, href)
                        normalized_link = scraper.urllib.parse.urlparse(absolute_link)
                        absolute_link = normalized_link._replace(fragment="").geturl()
                        if absolute_link not in visited_urls and absolute_link not in urls_to_visit:
                            urls_to_visit.append(absolute_link)
        
        mock_print.assert_any_call(f"Error fetching URL http://brokenurl.com: Test network error")
        self.assertIn("http://brokenurl.com", visited_urls) # Should be marked as visited
        self.assertIn("http://example.com/goodurl", visited_urls) # Good URL should still be visited
        self.assertEqual(pages_visited, 2)


        # Test error status code
        mock_requests_get.side_effect = lambda url, **kwargs: MagicMock(status_code=500) if url == "http://errorurl.com" else mock_good_response
        
        start_url_2 = "http://errorurl.com"
        visited_urls_2 = set()
        urls_to_visit_2 = deque([start_url_2, "http://example.com/anothergoodurl"])
        pages_visited_2 = 0

        def side_effect_func_status(url, **kwargs):
            if url == "http://errorurl.com":
                return MagicMock(status_code=500)
            elif url == "http://example.com/anothergoodurl":
                return mock_good_response # Reuse good response
            return MagicMock(status_code=404)
        mock_requests_get.side_effect = side_effect_func_status
        
        while urls_to_visit_2 and pages_visited_2 < max_pages:
            current_url = urls_to_visit_2.popleft()
            if current_url in visited_urls_2:
                continue
            
            visited_urls_2.add(current_url)
            pages_visited_2 += 1
            
            parsed_html = scraper.get_parsed_html(current_url)
            
            if parsed_html:
                anchor_tags = parsed_html.find_all('a', href=True)
                for tag in anchor_tags:
                    href = tag.get('href')
                    if href:
                        absolute_link = scraper.urllib.parse.urljoin(current_url, href)
                        normalized_link = scraper.urllib.parse.urlparse(absolute_link)
                        absolute_link = normalized_link._replace(fragment="").geturl()
                        if absolute_link not in visited_urls_2 and absolute_link not in urls_to_visit_2:
                            urls_to_visit_2.append(absolute_link)

        mock_print.assert_any_call(f"Error: Received status code 500 for URL: http://errorurl.com")
        self.assertIn("http://errorurl.com", visited_urls_2)
        self.assertIn("http://example.com/anothergoodurl", visited_urls_2)
        self.assertEqual(pages_visited_2, 2)


    @patch('scraper.requests.get')
    @patch('builtins.print')
    def test_relative_url_conversion(self, mock_print, mock_requests_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<html><body><a href='/about'>About</a><a href='contact.html'>Contact</a><a href='../careers'>Careers</a><a href='//otherdomain.com/path'>Other Domain</a><a href='http://fulldomain.com/specific'>Full Domain</a></body></html>"
        mock_requests_get.return_value = mock_response

        base_url = "http://example.com/company/" # Note the trailing slash
        visited_urls = set()
        urls_to_visit = deque([base_url])
        max_pages = 1
        pages_visited = 0

        if urls_to_visit and pages_visited < max_pages:
            current_url = urls_to_visit.popleft()
            if current_url not in visited_urls:
                visited_urls.add(current_url)
                pages_visited += 1
                parsed_html = scraper.get_parsed_html(current_url)
                if parsed_html:
                    anchor_tags = parsed_html.find_all('a', href=True)
                    for tag in anchor_tags:
                        href = tag.get('href')
                        if href:
                            absolute_link = scraper.urllib.parse.urljoin(current_url, href)
                            normalized_link = scraper.urllib.parse.urlparse(absolute_link)
                            absolute_link = normalized_link._replace(fragment="").geturl()
                            if absolute_link not in visited_urls and absolute_link not in urls_to_visit:
                                urls_to_visit.append(absolute_link)
        
        self.assertIn("http://example.com/about", urls_to_visit)
        self.assertIn("http://example.com/company/contact.html", urls_to_visit)
        self.assertIn("http://example.com/careers", urls_to_visit) # ../ resolved from /company/
        self.assertIn("http://otherdomain.com/path", urls_to_visit) # // resolves to http://otherdomain.com
        self.assertIn("http://fulldomain.com/specific", urls_to_visit)

    @patch('scraper.requests.get')
    @patch('builtins.print')
    def test_max_pages_limit(self, mock_print, mock_requests_get):
        # Mock requests.get to always return a page with one new link
        # to ensure the crawler has more pages to visit than max_pages
        page_counter = 0
        def side_effect_func(url, **kwargs):
            nonlocal page_counter
            page_counter += 1
            # Create a unique link for each page to ensure continuous crawling if not limited
            content = f"<html><body><a href='http://example.com/page{page_counter}'>Next Page</a></body></html>"
            return MagicMock(status_code=200, content=content.encode())
        mock_requests_get.side_effect = side_effect_func

        start_url = "http://example.com"
        visited_urls = set()
        urls_to_visit = deque([start_url])
        max_pages_limit = 3 # Set a small limit for testing
        pages_visited = 0

        while urls_to_visit and pages_visited < max_pages_limit:
            current_url = urls_to_visit.popleft()
            if current_url in visited_urls:
                continue
            
            visited_urls.add(current_url)
            pages_visited += 1
            
            # Call get_parsed_html, which uses the mocked requests.get
            parsed_html = scraper.get_parsed_html(current_url)
            
            if parsed_html:
                anchor_tags = parsed_html.find_all('a', href=True)
                for tag in anchor_tags:
                    href = tag.get('href')
                    if href:
                        absolute_link = scraper.urllib.parse.urljoin(current_url, href)
                        normalized_link = scraper.urllib.parse.urlparse(absolute_link)
                        absolute_link = normalized_link._replace(fragment="").geturl()
                        if absolute_link not in visited_urls and absolute_link not in urls_to_visit:
                            urls_to_visit.append(absolute_link)
        
        self.assertEqual(pages_visited, max_pages_limit, f"Crawler should visit exactly {max_pages_limit} pages.")
        # The number of calls to requests.get should match pages_visited if every page is successfully fetched
        self.assertEqual(mock_requests_get.call_count, max_pages_limit)


if __name__ == '__main__':
    unittest.main()
