from fastapi import FastAPI
from app.routers import chat, admin
from loguru import logger

app = FastAPI(title="Odysseus AK-AGI v5.0")

app.include_router(chat.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1/admin")

@app.on_event("startup")
async def startup_event():
    logger.info("Odysseus AK-AGI v5.0 Backend Started.")

@app.get("/")
async def root():
    return {"message": "Odysseus AK-AGI v5.0 Online", "protocol": "Iron God"}
