from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import items, production, inventory, dashboard

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(items.router)
app.include_router(production.router)
app.include_router(inventory.router)
app.include_router(dashboard.router)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
