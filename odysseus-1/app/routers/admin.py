import os
import shutil
from fastapi import APIRouter
from loguru import logger
import psutil

from app.services.grid_client import grid_client
from app.services.vault import vault

router = APIRouter()

@router.get("/health")
async def health():
    # swap, eBPF, Hydra queue, Soul temp
    vmem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    return {
        "status": "healthy",
        "hardware": {
            "memory_usage": vmem.percent,
            "swap_usage": swap.percent,
            "cpu_usage": psutil.cpu_percent()
        },
        "services": {
            "hydra_queue": 0, # Placeholder
            "soul_temp": 42.0, # Placeholder
            "ebpf_status": "active"
        }
    }

@router.get("/vault/status")
async def vault_status():
    # keys per provider
    # Note: In real app, we'd query the DB for counts
    return {
        "providers": ["github", "google", "groq", "cloudflare", "deepseek", "hf", "openrouter"],
        "status": "online"
    }

@router.post("/grid/checkpoint")
async def grid_checkpoint():
    # commit overlay
    logger.info("Grid: Committing overlay checkpoint...")
    # Simulation: in real life, might use rsync or filesystem snapshots
    return {"status": "checkpoint_created", "timestamp": os.urandom(4).hex()}

@router.post("/grid/rollback")
async def grid_rollback():
    # revert
    logger.warning("Grid: Reverting to last checkpoint...")
    return {"status": "rollback_complete"}
