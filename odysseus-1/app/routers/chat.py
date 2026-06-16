import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import orjson
from loguru import logger

from app.services.compiler import compiler
from app.services.soul_engine import soul_engine
from app.services.hydra import hydra

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_text = data.get("text", "")
    
    # 1. Compiler: parse intent
    dag = compiler.parse(user_text)
    
    # 2. SoulEngine: Local Inference
    soul_resp = await soul_engine.infer(user_text, dag)
    
    # 3. If requires cloud mass, Hydra: Dispatch
    cloud_results = None
    if dag.get("execution_target") == "cloud":
        cloud_results = await hydra.dispatch(dag)

    async def event_generator():
        # Stream Soul response tokens
        if "text" in soul_resp:
            yield f"data: {orjson.dumps({'type': 'soul', 'content': soul_resp['text']}).decode()}\n\n"
        
        # Stream Cloud results if any
        if cloud_results:
            yield f"data: {orjson.dumps({'type': 'hydra', 'content': cloud_results['text']}).decode()}\n\n"
            
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
