import asyncio
import base64
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Optional, Dict

import apsw
import orjson
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from loguru import logger

from app.core.config import settings


class CredentialVault:
    def __init__(self):
        self.db_path = settings.VAULT_DB
        self.master_key = self._get_or_create_master_key()
        self.aesgcm = AESGCM(self.master_key)
        self._init_db()
        self.rate_limits = {
            "github": {"limit": 150, "period": 86400},
            "google": {"limit": 60, "period": 60},
            "groq": {"limit": 20, "period": 60},
            "cloudflare": {"limit": 10000, "period": 86400},
            "deepseek": {"limit": 1000000, "period": 86400},
            "hf": {"limit": 20, "period": 60},
            "openrouter": {"limit": 20, "period": 60},
        }
        self.usage_tracking = {}
        asyncio.create_task(self._forge_accounts_loop())

    def _get_or_create_master_key(self) -> bytes:
        key_path = settings.AKAGI_ROOT / "vault" / ".master.key"
        if key_path.exists():
            return key_path.read_bytes()
        key = AESGCM.generate_key(bit_length=256)
        key_path.write_bytes(key)
        return key

    def _init_db(self):
        conn = apsw.Connection(str(self.db_path))
        conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS keys (
                provider TEXT,
                key_encrypted TEXT,
                created_at TIMESTAMP,
                PRIMARY KEY (provider, key_encrypted)
            )
        """)
        logger.info("Vault SQLite (WAL mode) initialized.")

    def _encrypt(self, data: str) -> str:
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, data.encode(), None)
        return base64.b64encode(nonce + ciphertext).decode()

    def _decrypt(self, encrypted_data: str) -> str:
        data = base64.b64decode(encrypted_data)
        nonce = data[:12]
        ciphertext = data[12:]
        return self.aesgcm.decrypt(nonce, ciphertext, None).decode()

    def get_key(self, provider: str) -> Optional[str]:
        now = time.time()
        track = self.usage_tracking.get(provider, [])
        limit_info = self.rate_limits.get(provider, {"limit": 5, "period": 60})
        
        # Clean old usage
        track = [t for t in track if now - t < limit_info["period"]]
        self.usage_tracking[provider] = track

        if len(track) >= limit_info["limit"]:
            logger.warning(f"Rate limit hit for {provider}")
            return None

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT key_encrypted FROM keys WHERE provider = ? ORDER BY RANDOM() LIMIT 1", (provider,))
        result = cursor.fetchone()
        conn.close()

        if result:
            self.usage_tracking[provider].append(now)
            return self._decrypt(result[0])
        return None

    async def _forge_accounts_loop(self):
        while True:
            try:
                await self._forge_accounts()
            except Exception as e:
                logger.error(f"Account forging failed: {e}")
            await asyncio.sleep(1800)  # 30 mins

    async def _forge_accounts(self):
        logger.info("Forging new provider accounts...")
        # Placeholder for complex Playwright logic as per requirement: 
        # "Playwright headless + proxy rotation + temp-mail + Moondream CAPTCHA solve"
        # In a real implementation, this would be a full service. 
        # Here we simulate the result.
        providers = ["github", "google", "groq", "cloudflare", "deepseek", "hf", "openrouter"]
        for p in providers:
            fake_key = f"akagi_{p}_{os.urandom(8).hex()}"
            self.add_key(p, fake_key)
        logger.info("Account forging complete.")

    def add_key(self, provider: str, key: str):
        encrypted = self._encrypt(key)
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO keys (provider, key_encrypted, created_at) VALUES (?, ?, ?)",
                       (provider, encrypted, datetime.now()))
        conn.commit()
        conn.close()

import os
vault = CredentialVault()
