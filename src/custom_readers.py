import requests
import logging
from typing import List 
from bs4 import BeautifulSoup

from llama_index.core import Document

import time
import requests
import logging
from bs4 import BeautifulSoup
from typing import List 
from llama_index.core import Document

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class BlogScraper:
    def __init__(self):
        self.base_url = 'http://omojumiller.com'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.posts = []

    def fetch_page(self, url):
        """Fetch a page with error handling and rate limiting"""
        try:
            time.sleep(2)  # Rate limiting
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logging.error(f"Error fetching {url}: {e}")
            return None

    def parse_post(self, post_element):
        """Extract information from a single blog post element"""
        try:
            # Find elements based on the actual HTML structure
            title_element = post_element.find('h1').find('a')
            title = title_element.get_text(strip=True)
            link = title_element['href']
            date_element = post_element.find('time')
            date = date_element.get_text(strip=True)
            description = post_element.find('p', class_='').get_text(strip=True)
            
            # Get full post content
            if link:
                post_page = self.fetch_page(link)
                if post_page:
                    post_soup = BeautifulSoup(post_page, 'html.parser')
                    # You might need to adjust this selector based on the article page structure
                    content_element = post_soup.find('div', class_='post') or post_soup.find('article')
                    full_content = content_element.get_text(strip=True, separator=' ') if content_element else ''
            
            return {
                'title': title,
                'link': link,
                'date': date,
                'description': description,
                'content': full_content if 'full_content' in locals() else ''
            }
        except Exception as e:
            logging.error(f"Error parsing post: {e}")
            return None

    def scrape_posts(self):
        """Main function to scrape all blog posts"""
        logging.info("Starting blog scraping")
        
        # Fetch the main page
        html = self.fetch_page(self.base_url)
        if not html:
            return

        soup = BeautifulSoup(html, 'html.parser')
        # Find the post list
        post_list = soup.find('ol', class_='post-list')
        if not post_list:
            logging.error("Could not find post list")
            return

        # Find all post items
        post_items = post_list.find_all('div', class_='deets')
        
        for post_item in post_items:
            post_data = self.parse_post(post_item)
            if post_data:
                self.posts.append(post_data)
                logging.info(f"Scraped post: {post_data['title']}")

        return self.save_posts()

    def save_posts(self)-> List[Document]:
        """Save scraped posts to a JSON file"""
        documents = []
        for post in self.posts:
            documents.append(Document(text=post['content']))
        
        return documents

