import multiprocessing
import os
import re
from pathlib import Path
from typing import Optional

from loguru import logger
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    AKAGI_ROOT: Path = Path("/akagi")
    MODEL_PATH: Path = Path("/akagi/soul/phi-3.5-mini.gguf")
    VAULT_DB: Path = Path("/akagi/vault/keys.db")
    LOG_LEVEL: str = "DEBUG"
    
    # Hardware limits
    CPU_CORES: int = multiprocessing.cpu_count()
    HAS_AVX2: bool = False

    def __init__(self, **values):
        super().__init__(**values)
        self.HAS_AVX2 = self._check_avx2()
        self._ensure_dirs()
        self._setup_logging()

    def _check_avx2(self) -> bool:
        try:
            with open("/proc/cpuinfo", "r") as f:
                content = f.read()
                return "avx2" in content.lower()
        except FileNotFoundError:
            return False

    def _ensure_dirs(self):
        for path in [self.AKAGI_ROOT, self.MODEL_PATH.parent, self.VAULT_DB.parent]:
            path.mkdir(parents=True, exist_ok=True)
            
    def _setup_logging(self):
        logger.remove()
        logger.add(
            self.AKAGI_ROOT / "logs" / "akagi.log",
            level=self.LOG_LEVEL,
            rotation="100 MB",
            retention="10 days",
            compression="zip"
        )
        logger.info(f"AK-AGI v5.0 Config Initialized. AVX2: {self.HAS_AVX2}, Cores: {self.CPU_CORES}")

    class Config:
        env_file = ".env"

settings = Settings()
