from typing import List, Dict
import pandas as pd

# Stock weights
STOCK_WEIGHT_REL_STRENGTH = 0.35
STOCK_WEIGHT_REV_GROWTH = 0.25
STOCK_WEIGHT_ROE = 0.20
STOCK_WEIGHT_ROIC = 0.20

# Sector weights
SECTOR_WEIGHT_REL_PERF = 0.40
SECTOR_WEIGHT_TREND = 0.30
SECTOR_WEIGHT_VOLATILITY = 0.30

# Trend scores
TREND_SCORES = {
    "Improving": 100,
    "Stable": 50,
    "Deteriorating": 0
}

def calculate_stock_scores(stocks: List[Dict]) -> List[Dict]:
    """
    Calculate composite scores and ranks for a list of stocks within the same sector.
    Expects stocks to be from the same sector for ranking purposes.
    """
    if not stocks:
        return []
    
    df = pd.DataFrame(stocks)
    
    # Ensure columns exist and fill NaNs
    cols_check = ['rel_strength_3m', 'revenue_growth', 'roe', 'roic']
    for col in cols_check:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = df[col].fillna(0.0)

    # Calculate percentile ranks (0-100)
    # rank(pct=True) returns 0.0 to 1.0. Multiply by 100.
    df['rel_strength_rank_pct'] = df['rel_strength_3m'].rank(pct=True) * 100
    df['revenue_growth_rank_pct'] = df['revenue_growth'].rank(pct=True) * 100
    df['roe_rank_pct'] = df['roe'].rank(pct=True) * 100
    df['roic_rank_pct'] = df['roic'].rank(pct=True) * 100
    
    # Calculate composite score
    df['composite_score'] = (
        (df['rel_strength_rank_pct'] * STOCK_WEIGHT_REL_STRENGTH) +
        (df['revenue_growth_rank_pct'] * STOCK_WEIGHT_REV_GROWTH) +
        (df['roe_rank_pct'] * STOCK_WEIGHT_ROE) +
        (df['roic_rank_pct'] * STOCK_WEIGHT_ROIC)
    )
    
    # Leader/Laggard
    # Leader >= 80, Laggard <= 30
    def categorize(score):
        if score >= 80:
            return "Leader"
        elif score <= 30:
            return "Laggard"
        else:
            return "Neutral" # Or just empty/middle
            
    df['leader_laggard'] = df['composite_score'].apply(categorize)
    
    # Rank within list
    df['rank'] = df['composite_score'].rank(ascending=False, method='min')
    
    return df.to_dict('records')

def calculate_sector_scores(sectors: List[Dict]) -> List[Dict]:
    """
    Calculate sector scores.
    """
    if not sectors:
        return []

    df = pd.DataFrame(sectors)
    
    # Example logic for sector scoring if not already provided
    # PRD says it uses rel_perf_3m_normalized, trend_score, volatility_rank_pct
    # We might not have volatility in input, assuming it's passed or we skip it if missing.
    
    # Check provided columns
    if 'rel_perf_3m' not in df.columns:
        return sectors # Can't calc
        
    # Normalize rel_perf_3m to 0-100 range for scoring? 
    # Or PRD implies specific normalization logic?
    # "rel_perf_3m_normalized"
    # Let's map min-max of rel_perf_3m to 0-100
    min_perf = df['rel_perf_3m'].min()
    max_perf = df['rel_perf_3m'].max()
    if max_perf != min_perf:
        df['rel_perf_normalized'] = (df['rel_perf_3m'] - min_perf) / (max_perf - min_perf) * 100
    else:
        df['rel_perf_normalized'] = 50.0
        
    df['trend_score_val'] = df['trend'].map(TREND_SCORES).fillna(50)
    
    # Volatility? If not present, maybe ignore or assume constant weight distribution adjust
    # For now, if missing, re-distribute weight? Or assume 50.
    vol_score = 50.0
    
    df['score_calculated'] = (
        (df['rel_perf_normalized'] * SECTOR_WEIGHT_REL_PERF) +
        (df['trend_score_val'] * SECTOR_WEIGHT_TREND) +
        (vol_score * SECTOR_WEIGHT_VOLATILITY) # Placeholder
    )
    
    # Note: PRD says "score" is in DB. We might not need to overwrite it if it's already there.
    # But for "live" data, we would.
    
    return df.to_dict('records')
