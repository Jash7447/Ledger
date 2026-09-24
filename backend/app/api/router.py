from fastapi import APIRouter

from app.api.routes import accounts, auth, budgets, classifications, dashboard, health, transactions

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(budgets.router, prefix="/budgets", tags=["budgets"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(
    transactions.router, prefix="/transactions", tags=["transactions"]
)
api_router.include_router(
    classifications.router, prefix="/classifications", tags=["classifications"]
)
