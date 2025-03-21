"""
Local Poe bot server implementation that can run multiple bots.
"""

from __future__ import annotations

import logging
from typing import AsyncIterable, Dict, Type
from pathlib import Path

import fastapi_poe as fp
from fastapi import FastAPI, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Import available bots
from echobot import EchoBot
from prompt_bot import PromptBot
from catbot import CatBot
from log_bot import LogBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Poe Bot Server")

# Mount static files
app.mount("/js", StaticFiles(directory="public/js"), name="js")
app.mount("/css", StaticFiles(directory="public/css"), name="css")

# Dictionary to store bot instances
BOTS: Dict[str, Type[fp.PoeBot]] = {
    "echo": EchoBot,
    "prompt": PromptBot,
    "cat": CatBot,
    "log": LogBot,
}

# Request counter for statistics
request_counter = 0

class HealthResponse(BaseModel):
    status: str
    available_bots: list[str]
    total_requests: int

@app.get("/", response_class=HTMLResponse)
async def admin_interface(request: Request):
    """Serve the admin interface."""
    try:
        admin_html_path = Path("public/admin.html")
        if admin_html_path.exists():
            return HTMLResponse(content=admin_html_path.read_text(), status_code=200)
        else:
            return HTMLResponse(content="Admin interface not found", status_code=404)
    except Exception as e:
        logger.error(f"Error serving admin interface: {str(e)}")
        return HTMLResponse(content="Error serving admin interface", status_code=500)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint that also returns available bots and statistics."""
    return {
        "status": "healthy",
        "available_bots": list(BOTS.keys()),
        "total_requests": request_counter
    }

@app.post("/bot/{bot_name}")
async def handle_bot_request(bot_name: str, request: fp.QueryRequest):
    """
    Handle bot requests by routing to the appropriate bot implementation.
    """
    global request_counter
    
    try:
        if bot_name not in BOTS:
            return Response(
                content=f"Bot '{bot_name}' not found. Available bots: {list(BOTS.keys())}",
                status_code=404
            )

        # Increment request counter
        request_counter += 1

        # Initialize the requested bot
        bot_class = BOTS[bot_name]
        bot = bot_class()

        # Get response from the bot
        responses: AsyncIterable[fp.PartialResponse] = await bot.get_response(request)
        
        # Convert AsyncIterable to a list for the response
        response_list = []
        async for response in responses:
            response_list.append(response.dict())
            logger.info(f"Bot {bot_name} response: {response.dict()}")

        return response_list

    except Exception as e:
        logger.error(f"Error processing request for bot {bot_name}: {str(e)}")
        return Response(
            content=f"Error processing request: {str(e)}",
            status_code=500
        )

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Poe Bot Server")
    logger.info(f"Available bots: {list(BOTS.keys())}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Poe Bot Server")