import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from datetime import date

class BBCParser:
    def __init__(self, base_url="https://www.bbc.com"):
        self.base_url = base_url
        self.news_url = urljoin(base_url, "/news")
        self.archive_base_url = urljoin(base_url, "/news/archive")
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_latest_links(self, limit=5):
        print(f"Fetching latest links from {self.news_url}...")
        try:
            response = requests.get(self.news_url, headers=self.headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching page {self.news_url}: {e}")
            return []

        soup = BeautifulSoup(response.content, 'lxml')
        links = set()
        for a_tag in soup.select('a[href*="/news/"]'):
            href = a_tag.get('href')
            if href:
                if '/live/' in href or '/av/' in href or '/topics/' in href:
                    continue
                if re.search(r'-\d{6,}', href) or '/articles/' in href:
                    full_url = urljoin(self.base_url, href)
                    links.add(full_url)
            if len(links) >= limit:
                break
        return list(links)[:limit]


    def parse_article(self, article_url):
        print(f"Parsing article: {article_url}")
        try:
            response = requests.get(article_url, headers=self.headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching article {article_url}: {e}")
            return None

        soup = BeautifulSoup(response.content, 'lxml')
        
        article_body = soup.find('article')
        if not article_body:
            article_body = soup.find('main', {'id': 'main-content'})
            if not article_body:
                return None

        title = article_body.find('h1')
        desc_tag = soup.find('meta', {'name': 'description'})
        author_tag = soup.find('meta', {'name': 'author'})
        date_tag = article_body.find('time')
        
        main_image_url = "N/A"
        og_image_tag = soup.find('meta', property='og:image')
        if og_image_tag and og_image_tag.has_attr('content'):
            main_image_url = og_image_tag['content']
        elif article_body:
            img_tag = article_body.find('img')
            if img_tag and img_tag.has_attr('src') and 'placeholder' not in img_tag['src']:
                main_image_url = img_tag['src']

        paragraphs = article_body.select('p')
        content_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
        
        return {
            "src": "BBC News", "link": article_url,
            "title": title.get_text(strip=True) if title else "N/A",
            "desc": desc_tag['content'] if desc_tag else "N/A",
            "author": author_tag['content'] if author_tag else "N/A",
            "creation_date": date_tag['datetime'] if date_tag else "N/A",
            "image": main_image_url, "content_for_analysis": content_text
        }