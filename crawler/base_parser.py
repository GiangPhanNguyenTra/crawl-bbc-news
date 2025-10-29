from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class BaseParser(ABC):
    
    @abstractmethod
    def get_latest_links(self, limit: int = 5) -> List[str]:
        """Lấy danh sách các link bài báo mới nhất."""
        pass

    @abstractmethod
    def parse_article(self, url: str) -> Optional[Dict]:
        """Phân tích một link bài báo và trả về dữ liệu có cấu trúc."""
        pass