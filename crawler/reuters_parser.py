import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import date, datetime

class ReutersParser:
    def __init__(self, base_url="https://www.reuters.com"):
        self.base_url = base_url
        self.news_url = f"{self.base_url}/world"

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_latest_links(self,limit=2):
        try:
            response = requests.get(self.news_url)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching page {self.news_url}: {e}")
            return []

        soup = BeautifulSoup(response.content, 'lxml')
        links = set()
        
        for a_tag in soup.find_all('a', {'data-testid': 'TitleLink'}):
            href = a_tag.get('href')
            if href:
                full_url = urljoin(self.base_url, href)
                links.add(full_url)
            if len(links) >= limit:
                break
        
        return list(links)

    def parse_article(self, article_url):
        print(f"Parsing article: {article_url}")
        try:
            response = requests.get(article_url, headers=self.headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching article {article_url}: {e}")
            return None

        soup = BeautifulSoup(response.content, 'lxml')
        
        title_tag = soup.find('h1', {'data-testid': 'Heading'})
        
        desc_text = "N/A"
        first_paragraph = soup.find('div', {'data-testid': 'paragraph-0'})
        if first_paragraph:
            desc_text = first_paragraph.get_text(strip=True)
        else:
            meta_desc_tag = soup.find('meta', {'name': 'description'})
            if meta_desc_tag:
                desc_text = meta_desc_tag['content']

        creation_date_iso = "N/A"
        time_tag = soup.find('time', {'data-testid': 'Body'})
        if time_tag and time_tag.has_attr('datetime'):
            creation_date_iso = time_tag['datetime']
        
        main_image_url = "N/A"
        og_image_tag = soup.find('meta', property='og:image')
        if og_image_tag and og_image_tag.has_attr('content'):
            main_image_url = og_image_tag['content']
        else:
            eager_image_tag = soup.find('img', {'data-testid': 'EagerImage'})
            if eager_image_tag and eager_image_tag.has_attr('src'):
                main_image_url = eager_image_tag['src']

        article_container = soup.find('div', {'data-testid': 'ArticleBody'})
        content_text = ""
        if article_container:
            paragraphs = article_container.select('div[data-testid^="paragraph-"]')
            content_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
        
        full_content_for_analysis = f"{title_tag.get_text(strip=True) if title_tag else ''}. {desc_text}. {content_text}"

        return {
            "src": "Reuters",
            "link": article_url,
            "title": title_tag.get_text(strip=True) if title_tag else "N/A",
            "desc": desc_text,
            "published_date": creation_date_iso,
            "image": main_image_url,
            "content_for_analysis": full_content_for_analysis 
        }