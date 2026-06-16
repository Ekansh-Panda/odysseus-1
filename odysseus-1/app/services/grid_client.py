import asyncio
import socket
import orjson
from loguru import logger
from app.core.config import settings

class GridClient:
    def __init__(self):
        self.sock_path = "/akagi/run/grid.sock"

    async def _send_command(self, command: str, params: dict) -> dict:
        try:
            reader, writer = await asyncio.open_unix_connection(self.sock_path)
            payload = orjson.dumps({"command": command, "params": params})
            writer.write(payload + b"\n")
            await writer.drain()
            
            data = await reader.readline()
            writer.close()
            await writer.wait_closed()
            
            return orjson.loads(data)
        except Exception as e:
            logger.error(f"GridClient error: {e}")
            return {"status": "error", "message": str(e)}

    async def mount_overlay(self, lower: str, upper: str, work: str, target: str):
        params = {
            "lower": lower,
            "upper": upper,
            "work": work,
            "target": target
        }
        return await self._send_command("MOUNT_OVERLAY", params)

    async def load_ebpf(self, prog_type: str, bytecode_base64: str):
        params = {
            "type": prog_type,
            "data": bytecode_base64
        }
        return await self._send_command("LOAD_EBPF", params)

    async def peripherals(self, action: str, data: dict = None):
        # SCREEN_SHOT, TYPE_STRING, MOUSE_MOVE, AUDIO_PLAY
        return await self._send_command(action, data or {})

grid_client = GridClient()
