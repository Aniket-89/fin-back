# Financial Concepts — Plain English Guide

This document explains what the app is measuring and why, without any code or tech jargon.

---

## The Big Picture

This app tracks **10 sectors of the Indian stock market** and helps you decide how to spread your money across them. The goal is to put more money in sectors that are gaining strength and less in sectors that are weakening — then keep your portfolio balanced over time.

---

## Sectors

A sector is a group of companies in the same industry. The app tracks these 10:

| Sector | What it covers | Weight in Indian economy |
|--------|----------------|--------------------------|
| IT | Software companies (TCS, Infosys, Wipro) | 14.5% |
| Banking & Financial Services | Banks and NBFCs (HDFC, ICICI, SBI) | 7.4% |
| Auto | Car and vehicle makers (Tata Motors, Maruti) | 6.8% |
| Pharma | Drug companies (Sun Pharma, Cipla) | 5.2% |
| FMCG | Everyday consumer goods (HUL, ITC, Nestle) | 8.1% |
| Energy | Oil, gas, and power (Reliance, ONGC, NTPC) | 9.3% |
| Infra | Construction and infrastructure (L&T, Adani Ports) | 11.2% |
| Metals | Steel and mining (Tata Steel, Hindalco) | 4.5% |
| Realty | Real estate developers (DLF, Godrej Properties) | 3.8% |
| Telecom | Media and telecom (Sun TV, Zee, Network18) | 2.9% |

**GVA Weight** (the % column above) = how much that sector contributes to India's total economic output (GDP). It's used as a starting point for deciding how much of your portfolio should go into each sector.

---

## The Score (0 to 100)

Every sector gets a score between 0 and 100.

- **50 = neutral** — the sector is moving exactly in line with the overall market (Nifty 50)
- **Above 50** = the sector is beating the market
- **Below 50** = the sector is lagging behind the market

**How it's calculated:** Start at 50, then add or subtract based on how much the sector outperformed or underperformed the Nifty 50 over the last 3 months. The result is capped between 0 and 100.

**Example:** If the IT sector grew 8% in 3 months but the Nifty 50 only grew 5%, that's a +3% outperformance. Score = 50 + (3 × 2) = 56.

---

## Trend: Improving / Stable / Deteriorating

The trend tells you whether a sector's momentum is getting better or worse right now.

| Trend | What it means |
|-------|---------------|
| **Improving** | The sector beat the market by more than 2% last month AND has been beating the market over the last 3 months. Momentum is building. |
| **Deteriorating** | The sector lagged the market by more than 2% last month AND has been lagging over the last 3 months. Momentum is fading. |
| **Stable** | Neither clearly improving nor deteriorating. Mixed signals or flat movement relative to the market. |

Think of it like a car's speedometer reading vs. the traffic average. Improving = you're going faster than traffic and speeding up. Deteriorating = you're going slower than traffic and slowing down. Stable = roughly keeping pace.

---

## Relative Performance

This measures how much a sector (or stock) gained or lost **compared to the Nifty 50**, not in absolute terms.

- **Positive number** = sector did better than the overall market
- **Negative number** = sector did worse than the overall market

It's measured over 4 time windows:
- **1 month** — recent momentum (is it picking up?)
- **3 months** — medium-term trend (is the story consistent?)
- **6 months** — medium-long trend
- **1 year** — full cycle view

**Why compare to Nifty 50?** Because the whole market goes up and down together. If a sector rose 10% but the Nifty also rose 10%, that sector didn't actually outperform — it just rode the wave. Relative performance strips out the market's overall movement to show only what's sector-specific.

---

## Stock Metrics

Each stock in the app has these measurements:

### Relative Strength (1 month / 3 months)
Same idea as relative performance above, but for an individual stock vs. the Nifty 50. A positive relative strength means the stock is outperforming the market.

### Market Cap (in Crores ₹)
The total value of the company on the stock market.
- 1 Crore = ₹10 million
- Example: TCS has a market cap of ~₹14,00,000 Cr (₹14 lakh crore) — one of India's biggest companies

### Revenue Growth (%)
How much the company's total sales grew compared to the previous year. Higher is better — it means the business is expanding.

### ROE — Return on Equity (%)
How much profit the company makes for every rupee shareholders have invested.
- ROE of 20% = the company earns ₹20 profit for every ₹100 of shareholder money
- Higher ROE = more efficient use of shareholder money

### ROIC — Return on Invested Capital (%)
Similar to ROE but looks at ALL capital invested — including debt, not just shareholder money. It's a more complete measure of how well management is using the total money in the business.
- ROIC above the cost of borrowing = the company is genuinely creating value
- ROIC below borrowing cost = the company is destroying value

### Liquidity Score (1–10)
How easily you can buy or sell the stock without the price moving against you.
- High score (8–10) = the stock trades in large volumes, easy to enter and exit
- Low score (1–4) = thin trading, buying or selling a large amount will move the price

---

## Leader vs. Laggard

Within each sector, stocks are ranked against their peers.

- **Leader** = a stock that is outperforming most other stocks in its sector
- **Laggard** = a stock that is underperforming most other stocks in its sector

If IT as a sector is doing well overall, you'd prefer to hold the Leaders (TCS, Infosys at their best) rather than the Laggards.

---

## Portfolio Concepts

### Holdings
The stocks you actually own — how many shares (quantity) and at what average purchase price (avg cost).

### P&L % (Profit and Loss)
How much you've made or lost on a stock since you bought it, expressed as a percentage.
- P&L of +15% = you're up 15% on that investment
- P&L of -8% = you're down 8%

### Target Weight
What percentage of your total portfolio *should* be in a given stock or sector according to your strategy.
- If Banking has a target weight of 10%, that means ₹10 of every ₹100 in the portfolio should be in banking stocks

---

## Portfolio Constraints (Guard Rails)

These are rules that prevent the portfolio from becoming too concentrated or risky:

| Rule | Value | What it prevents |
|------|-------|-----------------|
| **Max stock weight** | 7.5% | No single stock can be more than 7.5% of the total portfolio. Prevents over-reliance on one company. |
| **Max sector cap** | 30% | No single sector can exceed 30% of the portfolio. Prevents betting too heavily on one industry. |
| **Min liquidity ratio** | 10× | The stock must trade at least 10 times your position size in daily volume. Ensures you can exit without crashing the price. |
| **Max trades per rebalance** | 10 | Limits how many buy/sell actions are suggested at once. Keeps transaction costs manageable. |
| **Drift alert threshold** | 2% | If a sector drifts more than 2% from its target weight, it's flagged in yellow/red. Triggers a review. |

---

## Rebalancing

Over time, some stocks grow faster than others, causing your portfolio weights to drift away from targets. Rebalancing is the process of correcting this:

1. The app compares your **actual weights** (what you currently hold) against your **target weights** (what you want to hold)
2. It suggests **BUY** actions for sectors/stocks that are underweight
3. It suggests **SELL** actions for sectors/stocks that are overweight
4. Suggestions respect all the constraints above (max weight, liquidity, etc.)

**Example:** You want 10% in Banking but it's grown to 14%. The rebalancer suggests selling some banking stocks to bring it back to 10%, and using that money to top up an underweight sector.

---

## Rank in Sector

Each stock is ranked within its sector from 1 (best) to N (worst), and given a **percentile** score.

- Rank 1 of 5 = top performer in the sector, 100th percentile
- Rank 5 of 5 = weakest performer, 0th percentile

This helps you quickly see whether the stock you're looking at is a sector leader or a sector laggard.
