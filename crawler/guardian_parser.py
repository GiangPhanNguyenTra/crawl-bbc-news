# crawler/guardian_parser.py
import requests
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from urllib.parse import urljoin
from datetime import datetime
from crawler.base_parser import BaseParser

def _format_date(date_str: str) -> str:
    if not date_str:
        return "N/A"
    try:
        dt_object = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt_object.strftime('%Y-%m-%dT%H:%M:%SZ')
    except (ValueError, TypeError):
        return date_str

class GuardianParser(BaseParser):
    def __init__(self):
        self.base_url = "https://www.theguardian.com"
        self.news_url = f"{self.base_url}/world"

    def get_latest_links(self, limit: int = 5) -> List[str]:
        try:
            response = requests.get(self.news_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            links = []
            for a in soup.select('a[data-link-name="article"]', href=True):
                link = a['href']
                if not link.startswith('http'):
                    link = urljoin(self.base_url, link)
                if link not in links:
                    links.append(link)
                if len(links) >= limit:
                    break
            return links
        except Exception:
            return []

    def _get_date_from_url(self, url: str) -> Optional[str]:
        match = re.search(r'/(\d{4})/(\w{3})/(\d{2})/', url)
        if match:
            year, month_str, day = match.groups()
            month_map = {
                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
                'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
            }
            month = month_map.get(month_str.lower())
            if month:
                return f"{year}-{month}-{day}T00:00:00Z"
        return None

    def _find_main_image(self, soup: BeautifulSoup) -> str:
        # Ưu tiên 1: Thẻ <picture> cho ảnh chất lượng cao
        picture_tag = soup.find('picture', {'class': 'dcr-1989456'})
        if picture_tag:
            source_tag = picture_tag.find('source', {'srcset': True})
            if source_tag:
                return source_tag['srcset'].split(',')[0].split(' ')[0]

        # Ưu tiên 2: Tìm theo cơ chế Lightbox mà bạn đã phát hiện
        lightbox_link = soup.select_one('a.open-lightbox[href^="#img-"]')
        if lightbox_link:
            image_id = lightbox_link.get('href', '').lstrip('#')
            if image_id:
                image_container = soup.find(id=image_id)
                if image_container and image_container.find('img'):
                    img_tag = image_container.find('img')
                    if img_tag and img_tag.has_attr('src'):
                        return img_tag['src']

        # Ưu tiên 3: Tìm trong thẻ <figure> tiêu chuẩn
        figure_tag = soup.find('figure')
        if figure_tag and figure_tag.find('img'):
            img_tag = figure_tag.find('img')
            if img_tag and img_tag.has_attr('src'):
                return img_tag['src']

        # Ưu tiên 4 (Dự phòng cuối cùng): Tìm bất kỳ ảnh nào từ CDN của Guardian
        cdn_img = soup.find('img', src=re.compile(r'https://i\.guim\.co\.uk/img/'))
        if cdn_img:
            return cdn_img['src']
            
        return ""

    def parse_article(self, url: str) -> Optional[Dict]:
        print(f"Parsing article: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title_tag = soup.find('h1')
            title = title_tag.get_text(strip=True) if title_tag else "N/A"
            
            published_date_str = "N/A"
            time_tag = soup.find('time')
            if time_tag and time_tag.has_attr('datetime'):
                published_date_str = time_tag['datetime']
            else:
                date_from_url = self._get_date_from_url(url)
                if date_from_url:
                    published_date_str = date_from_url
            
            published_date = _format_date(published_date_str)

            summary_tag = soup.select_one('div[data-gu-name="standfirst"] p, div#maincontent p')
            desc = summary_tag.get_text(strip=True) if summary_tag else ""
            
            image_src = self._find_main_image(soup)
            
            content_div = soup.find('div', id='maincontent')
            content_for_analysis = ""
            if content_div:
                content_blocks = content_div.find_all('p')
                content_for_analysis = " ".join([block.get_text(" ", strip=True) for block in content_blocks])

            return {
                "title": title,
                "desc": desc,
                "published_date": published_date,
                "url": url,
                "source": "The Guardian",
                "image": image_src,
                "content_for_analysis": f"{title}. {desc} {content_for_analysis}"
            }
        except Exception:
            return None