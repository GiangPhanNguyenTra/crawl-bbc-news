import requests
from fastapi import FastAPI, HTTPException
from datetime import date, datetime, time
from typing import List

from crawler.bbc_parser import BBCParser
from crawler.guardian_parser import GuardianParser
from crawler.reuters_parser import ReutersParser
from crawler.word_analyzer import WordAnalyzer
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import news_collection

app = FastAPI(
    title="News Crawler & Enrichment API",
    description="API để crawl, làm giàu dữ liệu và lưu trữ tin tức.",
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

def _enrich_and_store_articles(articles: List[dict]) -> List[dict]:
    if not articles or not analyzer:
        return []

    corpus = [article.get('content_for_analysis', '') for article in articles]
    all_keywords_lists = analyzer.extract_keywords_with_tfidf(corpus)

    unique_words_to_enrich = set(word for keywords in all_keywords_lists for word in keywords)

    word_details_map = {}
    if unique_words_to_enrich:
        try:
            response = requests.post(settings.ENRICH_API_URL, json={"words": list(unique_words_to_enrich)})
            response.raise_for_status()
            enrich_results = response.json().get("results", [])
            word_details_map = {result['word']: result for result in enrich_results}
        except requests.RequestException as e:
            print(f"Could not call enrichment API: {e}")

    crawled_on_date = date.today().isoformat()
    final_articles = []
    for i, article in enumerate(articles):
        enriched_words = [word_details_map.get(word) for word in all_keywords_lists[i] if word in word_details_map]
        article['list_words'] = enriched_words
        del article['content_for_analysis']
        
        article['crawled_date'] = crawled_on_date
        news_collection.replace_one({'link': article['link']}, article, upsert=True)
        final_articles.append(article)
    
    return final_articles

@app.get("/crawl/bbc", summary="Crawl 1 tin tức mới nhất từ BBC News")
def crawl_latest_bbc_news():
    if not PARSERS: raise HTTPException(status_code=500, detail="Server not configured properly.")
    parser = PARSERS["bbc"]
    latest_links = parser.get_latest_links( limit=1)
    
    crawled_articles = [parser.parse_article(link) for link in latest_links if link]
    crawled_articles = [article for article in crawled_articles if article]

    return _enrich_and_store_articles(crawled_articles)

@app.get("/crawl/guardian", summary="Crawl 2 tin tức mới nhất từ The Guardian")
def crawl_latest_guardian_news():
    if not PARSERS: raise HTTPException(status_code=500, detail="Server not configured properly.")
    parser = PARSERS["guardian"]
    latest_links = parser.get_latest_links( limit=2)

    crawled_articles = [parser.parse_article(link) for link in latest_links if link]
    crawled_articles = [article for article in crawled_articles if article]

    return _enrich_and_store_articles(crawled_articles)

@app.get("/crawl/reuters", summary="Crawl 2 tin tức mới nhất từ Reuters")
def crawl_latest_reuters_news():
    if not PARSERS: raise HTTPException(status_code=500, detail="Server not configured properly.")
    parser = PARSERS["reuters"]
    latest_links = parser.get_latest_links( limit=2)

    crawled_articles = [parser.parse_article(link) for link in latest_links if link]
    crawled_articles = [article for article in crawled_articles if article]

    return _enrich_and_store_articles(crawled_articles)

@app.get("/articles/{query_date}", summary="Lấy danh sách các báo đã crawl trong ngày từ DB")
def get_articles_by_date(query_date: date):
    query_date_str = query_date.isoformat()
    
    query = { "crawled_date": query_date_str }
    
    articles = list(news_collection.find(query, {'_id': 0}))

    if not articles:
        return {"message": f"No articles were crawled on {query_date_str}."}
    return articles

@app.get("/", summary="Trạng thái API", include_in_schema=False)
def read_root():
    return {"status": "News Crawler API is running."}