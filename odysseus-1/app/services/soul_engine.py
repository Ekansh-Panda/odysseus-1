import asyncio
import time
from typing import Dict, Any, List, Optional

import orjson
import zmq
import zmq.asyncio
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings


class SoulEngine:
    def __init__(self):
        self.ctx = zmq.asyncio.Context()
        self.req = self.ctx.socket(zmq.REQ)
        self.req.connect("tcp://localhost:5555")
        
        self.ctrl = self.ctx.socket(zmq.PUSH)
        self.ctrl.connect("tcp://localhost:5556")
        
        self.state = {
            "working_memory": [],
            "long_term_memory": [],
            "perceptual_buffer": {},
            "emotional_state": {"valence": 0.0, "arousal": 0.0},
            "intent_buffer": [],
            "tool_registry": {},
            "system_prompts": {},
            "evolution_metrics": {}
        }
        
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(self.nightly_evolution, 'cron', hour=3)
        self.scheduler.start()

    async def infer(self, user_input: str, dag: Dict[str, Any]):
        payload = {
            "input": user_input,
            "dag": dag,
            "state": self.state
        }
        
        await self.req.send(orjson.dumps(payload))
        response_bytes = await self.req.recv()
        response = orjson.loads(response_bytes)
        
        # Update internal state
        self._update_state(response)
        
        return response

    def _update_state(self, response: Dict[str, Any]):
        if "state_delta" in response:
            for k, v in response["state_delta"].items():
                if isinstance(v, list):
                    self.state[k].extend(v)
                    self.state[k] = self.state[k][-100:] # Cap memory
                else:
                    self.state[k] = v
        logger.debug("Soul State updated.")

    async def nightly_evolution(self):
        logger.info("Starting Nightly Evolution (LoRA training)...")
        # Simulate LoRA trainer trigger
        # /akagi/soul/lora_trainer rank16
        await asyncio.sleep(5)
        self.ctrl.send(orjson.dumps({"command": "lora_update", "path": "/akagi/soul/latest.bin"}))
        logger.info("Hot-reload signal sent to Soul Daemon.")

    def safety_check(self, dag: Dict[str, Any]) -> bool:
        # ALLOW/CONFIRM/DENY logic
        for node in dag.get("nodes", []):
            intent = node.get("intent", "")
            if intent.startswith("kernel_"):
                return False # DENY critical kernel ops without confirmation
        return True

soul_engine = SoulEngine()
