from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import sectors, stocks, portfolio, rebalance, audit

app = FastAPI(title="India Sector Insights & Portfolio Rebalancing")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(sectors.router, prefix="/api/sectors", tags=["sectors"])
app.include_router(stocks.router, prefix="/api/stocks", tags=["stocks"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(rebalance.router, prefix="/api/rebalance", tags=["rebalance"])
app.include_router(audit.router, prefix="/api", tags=["audit"]) # Audit is at /api/audit-log and constraints

@app.get("/")
def root():
    return {"message": "System is running"}
