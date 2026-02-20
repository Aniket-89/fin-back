from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class SectorDataProvider(ABC):
    @abstractmethod
    def get_all_sectors(self, period: str = "3m") -> List[Dict]:
        """Get all sectors with performance metrics for the given period."""
        pass

    @abstractmethod
    def get_sector_details(self, sector_id: int) -> Optional[Dict]:
        """Get details for a single sector including history."""
        pass

class StockDataProvider(ABC):
    @abstractmethod
    def get_stocks_for_sector(self, sector_id: int) -> List[Dict]:
        """Get all stocks for a specific sector."""
        pass

    @abstractmethod
    def get_stock_details(self, ticker: str) -> Optional[Dict]:
        """Get details for a single stock including history."""
        pass

class PortfolioDataProvider(ABC):
    @abstractmethod
    def get_holdings(self) -> List[Dict]:
        """Get current portfolio holdings."""
        pass

    @abstractmethod
    def get_targets(self) -> Dict[str, float]:
        """Get target weights for sectors/stocks."""
        pass

class FundamentalsDataProvider(ABC):
    @abstractmethod
    def get_fundamentals(self, ticker: str) -> Dict:
        """Get fundamental data for a stock."""
        pass
