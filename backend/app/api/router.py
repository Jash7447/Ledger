from fastapi import APIRouter

from app.api.routes import (
    accounts,
    analytics,
    auth,
    budgets,
    classifications,
    dashboard,
    education,
    goals,
    health,
    people,
    recurring,
    settings,
    transactions,
)

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(budgets.router, prefix="/budgets", tags=["budgets"])
api_router.include_router(recurring.router, prefix="/recurring", tags=["recurring"])
api_router.include_router(education.router, prefix="/education", tags=["education"])
api_router.include_router(goals.router, prefix="/goals", tags=["goals"])
api_router.include_router(people.router, prefix="/people", tags=["people"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(
    transactions.router, prefix="/transactions", tags=["transactions"]
)
api_router.include_router(
    classifications.router, prefix="/classifications", tags=["classifications"]
)
