import json
from crawler.bbc_parser import BBCParser
from crawler.word_analyzer import WordAnalyzer

def main():
    CEFR_CSV_PATH = 'data/word_list_cefr_clean.csv'
    analyzer = WordAnalyzer(cefr_word_list_path=CEFR_CSV_PATH)
    parser = BBCParser()

    article_links = parser.get_article_links(limit=5)

    if not article_links:
        print("No articles found. Exiting.")
        return

    crawled_data = []
    
    for link in article_links:
        article_data = parser.parse_article(link)
        
        if article_data:
            content = article_data.pop('content_for_analysis')
            
            known_words = analyzer.find_known_words(content, limit=20)
            
            article_data['list_words'] = known_words
            
            crawled_data.append(article_data)
            print("-" * 50)

    print("\n\n===== CRAWLING COMPLETE. RESULTS: =====\n")
    print(json.dumps(crawled_data, indent=2, ensure_ascii=False))

    with open('crawled_news.json', 'w', encoding='utf-8') as f:
        json.dump(crawled_data, f, indent=2, ensure_ascii=False)
    print("\nResults also saved to crawled_news.json")


if __name__ == "__main__":
    main()