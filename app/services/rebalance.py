from typing import List, Dict, Any
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class Suggestion:
    action: str
    ticker: str
    quantity: int
    est_value_cr: float
    rationale: str
    binding_constraint: str = None
    post_trade_weight: float = 0.0
    post_trade_drift: float = 0.0

def generate_suggestions(
    holdings: List[Dict],
    sector_exposure: List[Dict],
    stocks: List[Dict],
    constraints: Dict[str, float]
) -> List[Dict]:
    """
    Generate rebalancing suggestions based on portfolio state and constraints.
    """
    # Parse constraints
    MAX_STOCK_WEIGHT = float(constraints.get('max_stock_weight', 7.5))
    MAX_SECTOR_CAP = float(constraints.get('max_sector_cap', 30.0))
    MIN_TRADE_SIZE_CR = 0.5 # Hardcoded in v1
    MAX_TRADES = int(constraints.get('max_trades_per_run', 10))
    
    suggestions = []
    
    # helper map
    stock_map = {s['ticker']: s for s in stocks}
    holding_map = {h['ticker']: h for h in holdings}
    
    # 1. Compute drift per sector (already provided in sector_exposure usually, but let's verify)
    # sector_exposure expected to have: sector_id, sector_name, actual_weight, target_weight
    
    sectors_by_drift = []
    for sec in sector_exposure:
        drift = sec['actual_weight'] - sec['target_weight']
        sectors_by_drift.append({
            **sec,
            'drift_val': drift,
            'abs_drift': abs(drift)
        })
        
    # 2. Sort by abs(drift) descending
    sectors_by_drift.sort(key=lambda x: x['abs_drift'], reverse=True)
    
    total_portfolio_value_cr = sum(h.get('current_value_cr', 0) for h in holdings) if holdings else 0
    if total_portfolio_value_cr == 0:
        return []

    # Track simulated weights
    sim_holdings = {h['ticker']: h.get('portfolio_weight', 0) for h in holdings}
    sim_sector_weights = {s['sector_id']: s['actual_weight'] for s in sector_exposure}

    trades_count = 0
    
    for sec in sectors_by_drift:
        if trades_count >= MAX_TRADES:
            break
            
        drift = sec['drift_val']
        sector_id = sec['sector_id']
        
        # Get stocks in this sector
        sector_stocks = [s for s in stocks if s.get('sector_id') == sector_id]
        
        if drift > 0:
            # Overweight -> SELL Laggards
            candidates = [s for s in sector_stocks if s.get('leader_laggard') == 'Laggard']
            # Sort by lowest score (worst first)
            candidates.sort(key=lambda s: s.get('composite_score', 0))
            action = 'SELL'
        else:
            # Underweight -> BUY Leaders
            candidates = [s for s in sector_stocks if s.get('leader_laggard') == 'Leader']
            # Sort by highest score (best first)
            candidates.sort(key=lambda s: s.get('composite_score', 0), reverse=True)
            action = 'BUY'
            
        if not candidates:
            continue
            
        # Try to execute trades for this sector to reduce drift
        # Target drift reduction: 50% of drift
        target_drift_reduction = abs(drift) * 0.5
        # Value to trade
        target_trade_value_cr = (target_drift_reduction / 100.0) * total_portfolio_value_cr
        
        current_trade_value = 0
        
        for stock in candidates:
            if trades_count >= MAX_TRADES:
                break
            if current_trade_value >= target_trade_value_cr:
                break
                
            ticker = stock['ticker']
            price = stock.get('current_price', 0) 
            # Note: stock list from input might not have current_price if it came from 'stocks' table not holdings.
            # holdings has current_price.
            # If buying a new stock, we need its price. 
            # We assume 'stocks' input includes current_price or we look it up.
            # If not in holdings, we might need a way to get price.
            # For now assume 'stocks' has it (we need to ensure provider puts it there).
            
            # If not in stocks input, check holdings
            if not price and ticker in holding_map:
                price = holding_map[ticker]['current_price_cr'] * 10000000 # wait, price is absolute. value is cr.
                price = holding_map[ticker].get('current_price')

            # If still no price, skip (safeguard)
            if not price or price <= 0:
                continue

            # Calculate quantity
            # Max trade size for this stock limited by remaining target_trade_value
            remaining_val = target_trade_value_cr - current_trade_value
            
            # Also apply min trade size
            if remaining_val < MIN_TRADE_SIZE_CR:
                continue
                
            qty = int((remaining_val * 10000000) / price)
            trade_val_cr = (qty * price) / 10000000.0
            
            if trade_val_cr < MIN_TRADE_SIZE_CR:
                continue

            # Constraints check
            current_weight = sim_holdings.get(ticker, 0)
            
            if action == 'BUY':
                new_weight = current_weight + (trade_val_cr / total_portfolio_value_cr * 100)
                if new_weight > MAX_STOCK_WEIGHT:
                    # Cap quantity
                    allowed_weight_incr = MAX_STOCK_WEIGHT - current_weight
                    if allowed_weight_incr <= 0: continue
                    
                    trade_val_cr = (allowed_weight_incr / 100) * total_portfolio_value_cr
                    qty = int((trade_val_cr * 10000000) / price)
                    trade_val_cr = (qty * price) / 10000000.0
                    new_weight = current_weight + (trade_val_cr / total_portfolio_value_cr * 100)
                
                sim_holdings[ticker] = new_weight
                sim_sector_weights[sector_id] += (trade_val_cr / total_portfolio_value_cr * 100)
                rationale = f"Buy Leader in {sec['sector_name']} to reduce underweight. Score: {stock.get('composite_score')}."

            elif action == 'SELL':
                # Can only sell what we play
                if ticker not in holding_map:
                    continue
                
                # Don't sell more than we have
                max_qty = holding_map[ticker]['quantity']
                qty = min(qty, max_qty)
                trade_val_cr = (qty * price) / 10000000.0
                
                if trade_val_cr < MIN_TRADE_SIZE_CR:
                    # If liquidating remainder and it's small? 
                    # PRD says trade value >= min_trade_size_cr. 
                    continue

                new_weight = current_weight - (trade_val_cr / total_portfolio_value_cr * 100)
                sim_holdings[ticker] = new_weight
                sim_sector_weights[sector_id] -= (trade_val_cr / total_portfolio_value_cr * 100)
                rationale = f"Sell Laggard in {sec['sector_name']} to reduce overweight. Score: {stock.get('composite_score')}."
            
            suggestions.append({
                "action": action,
                "ticker": ticker,
                "quantity": qty,
                "est_value_cr": round(trade_val_cr, 2),
                "rationale": rationale,
                "post_trade_weight": round(sim_holdings[ticker], 2),
                "post_trade_drift": round(sim_sector_weights[sector_id] - sec['target_weight'], 2) 
            })
            
            current_trade_value += trade_val_cr
            trades_count += 1
            
    return suggestions
