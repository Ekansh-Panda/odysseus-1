import re
from pathlib import Path
from typing import Dict, Any, List

import orjson
from loguru import logger

from app.core.config import settings


class WorkflowCompiler:
    def __init__(self):
        self.manifest_path = settings.AKAGI_ROOT / "primitives" / "manifests"
        self.intents = self._load_intents()

    def _load_intents(self) -> Dict[str, str]:
        # In a real scenario, this would load 128 patterns.
        # We'll simulate with a few key ones.
        return {
            "kernel_exec": r"execute\s+(?P<cmd>.*)",
            "file_read": r"read\s+file\s+(?P<path>.*)",
            "network_get": r"fetch\s+(?P<url>.*)",
            "code_compile": r"compile\s+(?P<lang>.*)\s+in\s+(?P<file>.*)",
            "data_query": r"select\s+(?P<query>.*)",
            "control_click": r"click\s+(?P<target>.*)"
        }

    def parse(self, text: str) -> Dict[str, Any]:
        logger.debug(f"Compiling workflow: {text}")
        nodes = []
        for name, pattern in self.intents.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                node_id = f"node_{len(nodes)}"
                nodes.append({
                    "id": node_id,
                    "intent": name,
                    "params": match.groupdict(),
                    "manifest": self.load_manifest(name)
                })

        # Default fallback to general chat if no intent matched
        if not nodes:
            nodes.append({
                "id": "node_0",
                "intent": "general_chat",
                "params": {"prompt": text},
                "manifest": {}
            })

        dag = {
            "nodes": nodes,
            "edges": [],
            "execution_target": "local"
        }
        
        # Auto-set cloud if complex
        if len(nodes) > 3 or any(n["intent"] in ["code_compile", "data_query"] for n in nodes):
            dag["execution_target"] = "cloud"
            
        return dag

    def load_manifest(self, name: str) -> Dict[str, Any]:
        # Search in /akagi/primitives/manifests/**/*.json
        # For this implementation, we assume they are organized by category
        parts = name.split("_")
        category = parts[0]
        action = parts[1] if len(parts) > 1 else "default"
        
        path = self.manifest_path / category / f"{action}.json"
        if path.exists():
            return orjson.loads(path.read_bytes())
        
        logger.warning(f"Manifest not found for {name} at {path}")
        return {}

compiler = WorkflowCompiler()
