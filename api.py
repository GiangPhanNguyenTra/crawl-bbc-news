from fastapi import FastAPI, HTTPException
from datetime import date
from typing import List
from crawler.bbc_parser import BBCParser
from crawler.guardian_parser import GuardianParser
from crawler.reuters_parser import ReutersParser
from crawler.word_analyzer import WordAnalyzer
from fastapi.middleware.cors import CORSMiddleware

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

def _process_articles_with_tfidf(articles: List[dict]) -> List[dict]:
    if not articles or not analyzer:
        return []

    corpus = [article.get('content_for_analysis', '') for article in articles]
    all_keywords = analyzer.extract_keywords_with_tfidf(corpus)

    for i, article in enumerate(articles):
        article['list_words'] = all_keywords[i]
        del article['content_for_analysis']
    
    return articles

@app.get("/crawl/bbc", summary="Crawl 5 tin tức mới nhất từ BBC News")
def crawl_latest_bbc_news():
    if not PARSERS or not analyzer:
        raise HTTPException(status_code=500, detail="Server not configured properly.")

    parser = PARSERS["bbc"]
    latest_links = parser.get_latest_links( limit=5)
    
    crawled_articles = [parser.parse_article(link) for link in latest_links if link]
    crawled_articles = [article for article in crawled_articles if article]

    return _process_articles_with_tfidf(crawled_articles)

@app.get("/crawl/guardian", summary="Crawl 5 tin tức mới nhất từ The Guardian")
def crawl_latest_guardian_news():
    if not PARSERS or not analyzer:
        raise HTTPException(status_code=500, detail="Server not configured properly.")

    parser = PARSERS["guardian"]
    latest_links = parser.get_latest_links(limit=5)

    crawled_articles = [parser.parse_article(link) for link in latest_links if link]
    crawled_articles = [article for article in crawled_articles if article]

    return _process_articles_with_tfidf(crawled_articles)

@app.get("/crawl/reuters", summary="Crawl 5 tin tức mới nhất từ Reuters")
def crawl_latest_reuters_news():
    if not PARSERS or not analyzer:
        raise HTTPException(status_code=500, detail="Server not configured properly.")

    parser = PARSERS["reuters"]
    latest_links = parser.get_latest_links(limit=5)

    crawled_articles = [parser.parse_article(link) for link in latest_links if link]
    crawled_articles = [article for article in crawled_articles if article]

    return _process_articles_with_tfidf(crawled_articles)

@app.get("/", summary="Trạng thái API", include_in_schema=False)
def read_root():
    return {"status": "News Crawler API is running."}