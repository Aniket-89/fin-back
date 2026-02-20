import sys
import os
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np

# Add backend to path
sys.path.append(os.getcwd())

from app.db.session import SessionLocal, engine, Base
from app.models.models import Sector, SectorPerformance, Stock, StockPrice, PortfolioHolding, PortfolioTarget, Constraint

# Setup
def init_db():
    Base.metadata.create_all(bind=engine)

def seed_sectors(db: Session):
    print("Seeding sectors...")
    sectors_data = [
        {"name": "IT", "nifty_code": "^CNXIT", "gva_weight": 14.5},
        {"name": "Banking & Financial Services", "nifty_code": "^NSEBANK", "gva_weight": 7.4},
        {"name": "Auto", "nifty_code": "^CNXAUTO", "gva_weight": 6.8},
        {"name": "Pharma", "nifty_code": "^CNXPHARMA", "gva_weight": 5.2},
        {"name": "FMCG", "nifty_code": "^CNXFMCG", "gva_weight": 8.1},
        {"name": "Energy", "nifty_code": "^CNXENERGY", "gva_weight": 9.3},
        {"name": "Infra", "nifty_code": "^CNXINFRA", "gva_weight": 11.2},
        {"name": "Metals", "nifty_code": "^CNXMETAL", "gva_weight": 4.5},
        {"name": "Realty", "nifty_code": "^CNXREALTY", "gva_weight": 3.8},
        {"name": "Telecom", "nifty_code": "^CNXMEDIA", "gva_weight": 2.9},
    ]
    
    sectors = []
    for s in sectors_data:
        sector = Sector(**s)
        db.add(sector)
        sectors.append(sector)
    db.commit()
    
    return db.query(Sector).all()

def seed_sector_performance(db: Session, sectors):
    pass # performance will be fetched live via the new provider

def seed_stocks(db: Session, sectors):
    print("Seeding stocks...")
    
    real_stocks_map = {
        "^CNXIT": [("TCS.NS", "Tata Consultancy Services"), ("INFY.NS", "Infosys"), ("HCLTECH.NS", "HCL Tech"), ("WIPRO.NS", "Wipro"), ("TECHM.NS", "Tech Mahindra")],
        "^NSEBANK": [("HDFCBANK.NS", "HDFC Bank"), ("ICICIBANK.NS", "ICICI Bank"), ("SBIN.NS", "State Bank of India"), ("KOTAKBANK.NS", "Kotak Mahindra"), ("AXISBANK.NS", "Axis Bank")],
        "^CNXAUTO": [("TATAMOTORS.NS", "Tata Motors"), ("M&M.NS", "Mahindra & Mahindra"), ("MARUTI.NS", "Maruti Suzuki"), ("BAJAJ-AUTO.NS", "Bajaj Auto"), ("EICHERMOT.NS", "Eicher Motors")],
        "^CNXPHARMA": [("SUNPHARMA.NS", "Sun Pharma"), ("CIPLA.NS", "Cipla"), ("DRREDDY.NS", "Dr. Reddy's Labs"), ("DIVISLAB.NS", "Divi's Labs"), ("LUPIN.NS", "Lupin")],
        "^CNXFMCG": [("ITC.NS", "ITC"), ("HINDUNILVR.NS", "Hindustan Unilever"), ("NESTLEIND.NS", "Nestle India"), ("BRITANNIA.NS", "Britannia"), ("TATACONSUM.NS", "Tata Consumer Products")],
        "^CNXENERGY": [("RELIANCE.NS", "Reliance Industries"), ("ONGC.NS", "ONGC"), ("NTPC.NS", "NTPC"), ("POWERGRID.NS", "Power Grid Corp"), ("COALINDIA.NS", "Coal India")],
        "^CNXINFRA": [("LT.NS", "Larsen & Toubro"), ("BHARTIARTL.NS", "Bharti Airtel"), ("ULTRACEMCO.NS", "UltraTech Cement"), ("GRASIM.NS", "Grasim Industries"), ("ADANIPORTS.NS", "Adani Ports")],
        "^CNXMETAL": [("TATASTEEL.NS", "Tata Steel"), ("HINDALCO.NS", "Hindalco"), ("JSWSTEEL.NS", "JSW Steel"), ("VEDL.NS", "Vedanta"), ("SAIL.NS", "SAIL")],
        "^CNXREALTY": [("DLF.NS", "DLF"), ("GODREJPROP.NS", "Godrej Properties"), ("OBEROIRLTY.NS", "Oberoi Realty"), ("PRESTIGE.NS", "Prestige Estates"), ("PHOENIXLTD.NS", "Phoenix Mills")],
        "^CNXMEDIA": [("SUNTV.NS", "Sun TV Network"), ("ZEEL.NS", "Zee Ent"), ("PVRINOX.NS", "PVR Inox"), ("TV18BRDCST.NS", "TV18 Broadcast"), ("NETWORK18.NS", "Network18")]
    }

    stocks = []
    for sector in sectors:
        sector_stocks = real_stocks_map.get(sector.nifty_code, [])
        for ticker, name in sector_stocks:
            stock = Stock(
                ticker=ticker,
                name=name,
                sector_id=sector.id,
                market_cap_cr=random.uniform(50000, 1000000), # placeholder until provider fetch
                revenue_growth=random.uniform(5, 30),
                roe=random.uniform(10, 25),
                roic=random.uniform(8, 20),
                liquidity_score=random.uniform(5, 10)
            )
            db.add(stock)
            stocks.append(stock)
    db.commit()
    db.commit()
    return stocks

def seed_portfolio(db: Session, stocks, sectors):
    print("Seeding portfolio...")
    for sector in sectors:
        target_weight = 100.0 / len(sectors)
        pt = PortfolioTarget(sector_id=sector.id, target_weight=target_weight)
        db.add(pt)
    
    holdings_stocks = random.sample(stocks, 22)
    for stock in holdings_stocks:
        qty = int(random.uniform(50, 500))
        avg_cost = random.uniform(500, 3000)
        target_w = 4.0
        
        ph = PortfolioHolding(
            ticker=stock.ticker,
            quantity=qty,
            avg_cost=avg_cost,
            target_weight=target_w
        )
        db.add(ph)
    db.commit()

def seed_constraints(db: Session):
    print("Seeding constraints...")
    constraints = [
        ("max_stock_weight", 7.5, "Max % any single stock can be of portfolio"),
        ("max_sector_cap", 30.0, "Max % any sector can be of portfolio"),
        ("min_liquidity_ratio", 10.0, "Min daily volume / position size ratio"),
        ("max_trades_per_run", 10.0, "Max suggestions per rebalance run"),
        ("drift_alert_threshold", 2.0, "% drift that triggers a warning colour"),
    ]
    for k, v, d in constraints:
        c = Constraint(key=k, value=v, description=d)
        db.add(c)
    db.commit()

def main():
    # drop tables to ensure clean slate with real tickers for v1.2
    Base.metadata.drop_all(bind=engine)
    init_db()
    db = SessionLocal()
    try:
        sectors = seed_sectors(db)
        seed_sector_performance(db, sectors)
        stocks_list = seed_stocks(db, sectors)
        seed_portfolio(db, stocks_list, sectors)
        seed_constraints(db)
        print("Seeding complete.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
