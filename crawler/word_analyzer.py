import os
import pandas as pd
from typing import List, Dict

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

class WordAnalyzer:
    def __init__(self, cefr_word_list_path: str):
        self.lemmatizer = WordNetLemmatizer()
        
        self._download_nltk_data()

        self.stop_words = set(stopwords.words('english'))
        self.cefr_order = ['C2', 'C1', 'B2', 'B1', 'A2', 'A1']
        self.word_dict = self._load_word_list(cefr_word_list_path)
        print(f"Loaded {len(self.word_dict)} words from CEFR list.")
        
    def _download_nltk_data(self):
        try:
            stopwords.words('english')
            word_tokenize('test')
            self.lemmatizer.lemmatize('test')
        except LookupError as e:
            print(f"NLTK data component not found: {e}. Downloading required packages...")
            nltk.download('punkt')
            nltk.download('stopwords')
            nltk.download('wordnet')
            nltk.download('omw-1.4')
            print("NLTK data downloaded successfully.")
            self.stop_words = set(stopwords.words('english'))


    def _load_word_list(self, path: str) -> Dict[str, str]:
        try:
            df = pd.read_csv(path)
            return pd.Series(df.level.values, index=df.word.str.lower()).to_dict()
        except FileNotFoundError:
            print(f"FATAL: Word list file not found at {path}")
            raise
        except KeyError:
            print("FATAL: CSV must contain 'word' and 'level' columns.")
            raise

    def find_known_words(self, text_content: str, limit: int = 20) -> List[Dict[str, str]]:
        if not text_content:
            return []

        tokens = word_tokenize(text_content.lower())
        
        lemmatized_words = set()
        for token in tokens:
            if token.isalpha() and len(token) > 2 and token not in self.stop_words:
                lemma = self.lemmatizer.lemmatize(token)
                lemmatized_words.add(lemma)
        
        found_words = []
        for word in lemmatized_words:
            level = self.word_dict.get(word)
            if level in self.cefr_order:
                found_words.append(word)

        
        return found_words[:limit]