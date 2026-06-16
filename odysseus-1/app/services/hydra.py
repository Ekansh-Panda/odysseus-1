import asyncio
from typing import List, Dict, Any, Optional

import httpx
import orjson
from loguru import logger

from app.services.vault import vault


class HydraEngine:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(1000)
        self.client = httpx.AsyncClient(timeout=30.0)
        self.provider_keys = {
            "github": 200, "google": 50, "groq": 100, "cloudflare": 50,
            "deepseek": 20, "hf": 100, "openrouter": 10
        }

    async def dispatch(self, task_dag: Dict[str, Any]) -> Dict[str, Any]:
        results = {}
        nodes = task_dag.get("nodes", [])
        
        async def run_node(node):
            async with self.semaphore:
                intent = node.get("intent")
                provider = node.get("params", {}).get("provider", "openai") # default
                
                attempts = 0
                while attempts < 5:
                    api_key = vault.get_key(provider)
                    if not api_key:
                        provider = self._fallback_provider(provider)
                        attempts += 1
                        continue
                    
                    try:
                        response = await self.client.post(
                            self._get_endpoint(provider),
                            headers={"Authorization": f"Bearer {api_key}"},
                            json={"model": node.get("params", {}).get("model"), "messages": [{"role": "user", "content": node.get("params", {}).get("prompt")}]},
                        )
                        
                        if response.status_code in [429, 403]:
                            logger.warning(f"Bifrost Fallback triggered for {provider} (Status: {response.status_code})")
                            attempts += 1
                            await asyncio.sleep(2 ** attempts)
                            continue
                        
                        response.raise_for_status()
                        results[node["id"]] = response.json()
                        break
                    except Exception as e:
                        logger.error(f"Node {node['id']} failed: {e}")
                        attempts += 1
                        await asyncio.sleep(2 ** attempts)
                
        await asyncio.gather(*(run_node(n) for n in nodes))
        return self.map_reduce(results)

    def _fallback_provider(self, provider: str) -> str:
        options = [p for p in self.provider_keys.keys() if p != provider]
        import random
        return random.choice(options) if options else provider

    def _get_endpoint(self, provider: str) -> str:
        endpoints = {
            "github": "https://models.inference.ai.azure.com/chat/completions",
            "google": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            "groq": "https://api.groq.com/openai/v1/chat/completions",
            "cloudflare": "https://api.cloudflare.com/client/v4/accounts/akagi/ai/run/chat/completions",
            "deepseek": "https://api.deepseek.com/v1/chat/completions",
            "hf": "https://api-inference.huggingface.co/models/akagi/chat/completions",
            "openrouter": "https://openrouter.ai/api/v1/chat/completions"
        }
        return endpoints.get(provider, "https://api.openai.com/v1/chat/completions")

    def map_reduce(self, results: Dict[str, Any]) -> Dict[str, Any]:
        merged = {"text": "", "data": {}}
        for rid, res in results.items():
            if "choices" in res:
                merged["text"] += res["choices"][0]["message"]["content"] + "\n"
            if "data" in res:
                merged["data"].update(res["data"])
        return merged

hydra = HydraEngine()
