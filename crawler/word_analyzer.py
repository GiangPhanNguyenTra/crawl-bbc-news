import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import os

class WordAnalyzer:
    def __init__(self, cefr_word_list_path):
        self._download_nltk_data()
        
        print("Loading CEFR word list...")
        df = pd.read_csv(cefr_word_list_path)
        self.cefr_words = set(df['headword'].str.lower())
        print(f"Loaded {len(self.cefr_words)} words from CEFR list.")
        
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()

    def _download_nltk_data(self):
        required_packages = ['punkt', 'stopwords', 'wordnet', 'omw-1.4', 'punkt_tab']
        nltk_data_path = os.path.join(os.path.dirname(__file__), 'nltk_data')
        if not os.path.exists(nltk_data_path):
            os.makedirs(nltk_data_path)
        nltk.data.path.append(nltk_data_path)

        for package in required_packages:
            try:
                nltk.data.find(f'tokenizers/{package}')
            except LookupError:
                try:
                    nltk.data.find(f'corpora/{package}')
                except LookupError:
                    try:
                        nltk.data.find(f'corpora/{package}.zip')
                    except LookupError:
                        nltk.download(package, download_dir=nltk_data_path)

    def find_known_words(self, text, limit=20):
        if not text:
            return []

        tokens = word_tokenize(text.lower())
        lemmatized_words = []
        for token in tokens:
            if token.isalpha() and len(token) > 2 and token not in self.stop_words:
                lemma = self.lemmatizer.lemmatize(token)
                lemmatized_words.append(lemma)
        
        found_words = []
        added_words = set()
        for word in lemmatized_words:
            if len(found_words) >= limit:
                break
            if word in self.cefr_words and word not in added_words:
                found_words.append(word)
                added_words.add(word)
                
        return found_words