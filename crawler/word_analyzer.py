import pandas as pd
from keybert import KeyBERT
import nltk

class WordAnalyzer:
    def __init__(self, cefr_word_list_path):
        print("Loading CEFR word list...")
        df = pd.read_csv(cefr_word_list_path)
        self.cefr_words = set(df['word'].str.lower())
        self.lemmatizer = nltk.stem.WordNetLemmatizer()
        print(f"Loaded {len(self.cefr_words)} words from CEFR list.")
        
        print("Loading KeyBERT model (all-MiniLM-L6-v2)...")
        print("This may take a few minutes on the first run as the model is downloaded.")
        self.kw_model = KeyBERT(model='all-MiniLM-L6-v2')
        print("KeyBERT model loaded successfully.")

    def extract_keywords_with_tfidf(self, corpus_texts: list, limit_per_article=20):
        if not corpus_texts:
            return []

        all_final_keywords = []
        for text in corpus_texts:
            if not text or not isinstance(text, str) or len(text.split()) < 5:
                all_final_keywords.append([])
                continue
            
            try:
                keywords_with_scores = self.kw_model.extract_keywords(
                    text,
                    keyphrase_ngram_range=(1, 1),
                    stop_words='english',
                    top_n=100  
                )
                
                candidate_keywords = [kw for kw, score in keywords_with_scores]

                final_keywords = []
                added_lemmas = set() # Dùng để tránh thêm các từ trùng dạng gốc (vd: 'election' và 'elections')
                for keyword in candidate_keywords:
                    if len(final_keywords) >= limit_per_article:
                        break

                    lemma = self.lemmatizer.lemmatize(keyword)
                    
                    if lemma in self.cefr_words and lemma not in added_lemmas:
                        final_keywords.append(lemma)
                        added_lemmas.add(lemma)
                
                all_final_keywords.append(final_keywords)

            except Exception as e:
                print(f"Error processing text with KeyBERT: {e}")
                all_final_keywords.append([])

        return all_final_keywords