import pandas as pd
from keybert import KeyBERT
import nltk
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

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
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("KeyBERT model loaded successfully.")

    def extract_keywords_with_tfidf(self, corpus_texts: list, limit_per_article=20, similarity_threshold=0.2):
        if not corpus_texts:
            return []

        all_final_keywords = []
        for text in corpus_texts:
            if not text or not isinstance(text, str) or len(text.split()) < 5:
                all_final_keywords.append([])
                continue
            
            try:
                # Extract keywords with KeyBERT and their scores
                keywords_with_scores = self.kw_model.extract_keywords(
                    text,
                    keyphrase_ngram_range=(1, 1),
                    stop_words='english',
                    top_n=100  
                )
                
                if not keywords_with_scores:
                    all_final_keywords.append([])
                    continue
                
                # Get embedding of the original text
                text_embedding = self.embedding_model.encode(text)

                final_keywords = []
                added_lemmas = set()
                
                for keyword, keybert_score in keywords_with_scores:
                    if len(final_keywords) >= limit_per_article:
                        break

                    # Get embedding of keyword and compare with text embedding
                    keyword_embedding = self.embedding_model.encode(keyword)
                    
                    # Calculate cosine similarity between text and keyword embeddings
                    similarity = cosine_similarity(
                        text_embedding.reshape(1, -1),
                        keyword_embedding.reshape(1, -1)
                    )[0][0]
                    
                    # Filter by similarity threshold and CEFR word list
                    lemma = self.lemmatizer.lemmatize(keyword.lower())
                    
                    # Use lower threshold or KeyBERT score as alternative
                    if (similarity >= similarity_threshold or keybert_score >= 0.3) and lemma in self.cefr_words and lemma not in added_lemmas:
                        final_keywords.append(lemma)
                        added_lemmas.add(lemma)
                
                all_final_keywords.append(final_keywords)

            except Exception as e:
                print(f"Error processing text with KeyBERT: {e}")
                all_final_keywords.append([])

        return all_final_keywords