from typing import Union, List
import requests
from bs4 import BeautifulSoup

from llama_index.core import Document
from llama_index.readers.web import BeautifulSoupWebReader

def trim_spacing(text:str) -> str:
    return "\n".join([t for t in text.split("\n") if t])

def get_blog_post_links(base_url:str, subdomain:str = "/blog/"):
    blog_post_links = []
    page = requests.get(base_url)
    soup = BeautifulSoup(page.text, "html.parser")
    card_titles = soup.find_all(class_="card-title")
    next_page = soup.find("a", class_="pagination__next")

    stripped_url = base_url.replace(subdomain, "")
    
    for title in card_titles:
        if title.a:
            blog_post_links.append(stripped_url + title.a['href'])
    
    if next_page:
        blog_post_links.extend(
            get_blog_post_links(
                base_url.replace(subdomain, next_page['href']),
                next_page['href']
            )
        )

    return blog_post_links

def parse_blog_post(link:str):
    blog_elements = []
    page = requests.get(link)
    soup = BeautifulSoup(page.text, "html.parser")

    post_title = soup.find("h3", class_="title").get_text()
    post_body = soup.find("article", class_="blog-post").get_text()
    post_date = soup.find("h6", class_="category").get_text()

    return "\n".join([post_title, post_date, trim_spacing(post_body)])

class FimioBlogWebReader(BeautifulSoupWebReader):
    def __init__(self):
        super().__init__()

    def load_data(self, base_url:str, n:Union[bool, int] = None) -> List[Document]:
        documents = []
        blog_post_links = get_blog_post_links(base_url)
        if n:
            blog_post_links = blog_post_links[:n]

        for link in blog_post_links:
            try:
                blog_post = parse_blog_post(link)
                extra_info = {"URL": link}
            except Exception as e:
                raise ValueError(f"Failed to parse page at {link}.\nError: {e}")
            
            documents.append(Document(text=blog_post, id_=link, extra_info=extra_info))

        return documents