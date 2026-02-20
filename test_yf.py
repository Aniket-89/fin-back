import sys
import logging
logging.basicConfig(level=logging.INFO)

from app.db.session import SessionLocal
from app.providers.yfinance.sector import YfinanceSectorDataProvider
from app.providers.yfinance.stock import YfinanceStockDataProvider

print("Starting test...")
db = SessionLocal()

print("Testing Sector Provider...")
sp = YfinanceSectorDataProvider(db)
sectors = sp.get_all_sectors()
print(f"Sectors found: {len(sectors)}")
if len(sectors) > 0:
    print(sectors[0])

print("\nTesting Stock Provider...")
stp = YfinanceStockDataProvider(db)
# test with sector ID 1
stocks = stp.get_stocks_for_sector(1)
print(f"Stocks found: {len(stocks)}")
if len(stocks) > 0:
    print(stocks[0])

print("Finished test.")
