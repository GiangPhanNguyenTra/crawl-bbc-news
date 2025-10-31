import pandas as pd
import nltk
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer

class WordAnalyzer:
    def __init__(self, cefr_word_list_path):
        print("Loading CEFR word list...")
        df = pd.read_csv(cefr_word_list_path)
        self.cefr_words = set(df['word'].str.lower())
        print(f"Loaded {len(self.cefr_words)} words from CEFR list.")
        
        self.lemmatizer = WordNetLemmatizer()

    def _lemmatizing_tokenizer(self, text):
        tokens = nltk.word_tokenize(text.lower())
        return [self.lemmatizer.lemmatize(token) for token in tokens if token.isalpha()]

    def extract_keywords_with_tfidf(self, corpus_texts: list, limit_per_article=20):
        if not corpus_texts:
            return []

        # 1. Khởi tạo TfidfVectorizer
        vectorizer = TfidfVectorizer(
            tokenizer=self._lemmatizing_tokenizer,
            stop_words='english',
            max_df=0.8,
            min_df=2 
        )

        # 2. Học từ vựng và tính toán ma trận TF-IDF
        try:
            tfidf_matrix = vectorizer.fit_transform(corpus_texts)
        except ValueError:
            # Xảy ra khi corpus quá nhỏ hoặc không có từ nào đáp ứng min_df
            print("Warning: Could not build TF-IDF matrix. Corpus might be too small or empty.")
            return [[] for _ in corpus_texts]
            
        # Lấy danh sách tất cả các từ (features) mà vectorizer đã học được
        feature_names = vectorizer.get_feature_names_out()

        all_keywords = []
        # 3. Trích xuất từ khóa cho từng bài báo
        for doc_index in range(len(corpus_texts)):
            # Lấy vector TF-IDF cho bài báo hiện tại
            feature_vector = tfidf_matrix[doc_index]
            
            # Lấy chỉ số và điểm số của các từ có trong bài báo này
            # .tocoo() chuyển đổi ma trận thưa thành định dạng dễ duyệt hơn
            non_zero_indices = feature_vector.tocoo().col
            scores = feature_vector.tocoo().data

            # Tạo một list các tuple (từ, điểm số)
            word_score_pairs = [(feature_names[i], scores[idx]) for idx, i in enumerate(non_zero_indices)]
            
            # Sắp xếp các từ theo điểm số TF-IDF giảm dần
            sorted_word_scores = sorted(word_score_pairs, key=lambda x: x[1], reverse=True)

            # 4. Lọc kết quả: chỉ giữ lại các từ có trong danh sách CEFR
            doc_keywords = []
            for word, score in sorted_word_scores:
                if len(doc_keywords) >= limit_per_article:
                    break
                if word in self.cefr_words:
                    doc_keywords.append(word)
            
            all_keywords.append(doc_keywords)
            
        return all_keywords