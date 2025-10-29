from fastapi import FastAPI, HTTPException
from datetime import date
from typing import List
from crawler.bbc_parser import BBCParser
from crawler.word_analyzer import WordAnalyzer
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="BBC News Crawler API",
    description="API để crawl tin tức từ BBC News.",
    version="1.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    analyzer = WordAnalyzer(cefr_word_list_path='data/word_list_cefr_clean.csv')
    parser = BBCParser()
except FileNotFoundError:
    analyzer = None
    parser = None

def _process_links_and_get_data(article_links: List[str]) -> List[dict]:
    if not article_links:
        return []
    
    crawled_data = []
    for link in article_links:
        article_data = parser.parse_article(link)
        if article_data:
            content = article_data.pop('content_for_analysis')
            known_words = analyzer.find_known_words(content, limit=20)
            article_data['list_words'] = known_words
            crawled_data.append(article_data)
    return crawled_data

@app.get("/crawl/latest", summary="Crawl 5 tin tức mới nhất")
def crawl_latest_news():
    if not parser or not analyzer:
        raise HTTPException(status_code=500, detail="Server not configured properly.")

    latest_links = parser.get_latest_links(limit=5)
    return _process_links_and_get_data(latest_links)


@app.get("/", summary="Trạng thái API", include_in_schema=False)
def read_root():
    return {"status": "BBC News Crawler API is running."}