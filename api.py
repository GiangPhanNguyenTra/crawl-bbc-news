from fastapi import FastAPI, HTTPException
from datetime import date
from typing import List
from crawler.bbc_parser import BBCParser
from crawler.guardian_parser import GuardianParser
from crawler.reuters_parser import ReutersParser
from crawler.word_analyzer import WordAnalyzer
from fastapi.middleware.cors import CORSMiddleware
from crawler.base_parser import BaseParser

app = FastAPI(
    title="News Crawler API",
    description="API để crawl tin tức từ các nguồn báo uy tín.",
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
    PARSERS = {
        "bbc": BBCParser(),
        "guardian": GuardianParser(),
        "reuters": ReutersParser()
    }
except FileNotFoundError:
    analyzer = None
    PARSERS = None

def _process_links_and_get_data(parser: BaseParser, article_links: List[str]) -> List[dict]:
    if not article_links or not analyzer:
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


@app.get("/crawl/bbc", summary="Crawl 5 tin tức mới nhất từ BBC News")
def crawl_latest_bbc_news():
    if not PARSERS or not analyzer:
        raise HTTPException(status_code=500, detail="Server not configured properly.")

    bbc_parser = PARSERS["bbc"]
    latest_links = bbc_parser.get_latest_links(limit=5)
    return _process_links_and_get_data(bbc_parser, latest_links)

@app.get("/crawl/guardian", summary="Crawl 5 tin tức mới nhất từ The Guardian")
def crawl_latest_guardian_news():
    if not PARSERS or not analyzer:
        raise HTTPException(status_code=500, detail="Server not configured properly.")

    guardian_parser = PARSERS["guardian"]
    latest_links = guardian_parser.get_latest_links(limit=5)
    return _process_links_and_get_data(guardian_parser, latest_links)

@app.get("/crawl/reuters", summary="Crawl 5 tin tức mới nhất từ Reuters")
def crawl_latest_reuters_news():
    if not PARSERS or not analyzer:
        raise HTTPException(status_code=500, detail="Server not configured properly.")

    reuters_parser = PARSERS["reuters"]
    latest_links = reuters_parser.get_latest_links( limit=5)
    return _process_links_and_get_data(reuters_parser, latest_links)

@app.get("/", summary="Trạng thái API", include_in_schema=False)
def read_root():
    return {"status": "News Crawler API is running."}