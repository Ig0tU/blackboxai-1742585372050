"""
Local Poe bot server implementation that can run multiple bots.
"""

from __future__ import annotations

import logging
import json
from typing import AsyncIterable, Dict, Type, List
from pathlib import Path

import fastapi_poe as fp
from fastapi import FastAPI, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# Import available bots
from echobot import EchoBot
from prompt_bot import PromptBot
from catbot import CatBot
from log_bot import LogBot
from enterprise_wrapper_bot import EnterpriseWrapperBot
from app_creator_bot import AppCreatorBot

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

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
BOTS = {
    "echo": EchoBot,
    "prompt": PromptBot,
    "cat": CatBot,
    "log": LogBot,
    "enterprise": EnterpriseWrapperBot,
    "app-creator": AppCreatorBot,
}

# Bot descriptions for the admin interface
BOT_DESCRIPTIONS = {
    "echo": "Simple bot that echoes back messages",
    "prompt": "Bot that uses a template to format responses",
    "cat": "Fun bot that responds with cat facts and behaviors",
    "log": "Demonstration bot that logs all interactions",
    "enterprise": "Advanced bot that can use GPT-4 and Claude models",
    "app-creator": "Poe App Creator integration for building and managing apps",
}

# Request counter for statistics
request_counter = 0

class HealthResponse(BaseModel):
    status: str
    available_bots: List[str]
    total_requests: int
    bot_descriptions: Dict[str, str]

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

@app.get("/health")
async def health_check():
    """Health check endpoint that also returns available bots and statistics."""
    response_data = {
        "status": "healthy",
        "available_bots": sorted(list(BOTS.keys())),  # Convert to sorted list for consistent order
        "total_requests": request_counter,
        "bot_descriptions": BOT_DESCRIPTIONS
    }
    logger.info(f"Health check response: {response_data}")
    return JSONResponse(content=response_data)

@app.post("/bot/{bot_name}")
async def handle_bot_request(bot_name: str, request: fp.QueryRequest):
    """
    Handle bot requests by routing to the appropriate bot implementation.
    """
    global request_counter
    
    try:
        if bot_name not in BOTS:
            return JSONResponse(
                content={
                    "error": f"Bot '{bot_name}' not found",
                    "available_bots": sorted(list(BOTS.keys()))
                },
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
            if isinstance(response, fp.PartialResponse):
                response_list.append({"text": response.text})
            elif isinstance(response, str):
                response_list.append({"text": response})
            else:
                response_list.append({"text": str(response)})
            logger.info(f"Bot {bot_name} response: {response_list[-1]}")

        # Ensure we have at least one response
        if not response_list:
            response_list.append({"text": "No response generated"})

        return JSONResponse(content=response_list)

    except Exception as e:
        logger.error(f"Error processing request for bot {bot_name}: {str(e)}")
        return JSONResponse(
            content={"error": f"Error processing request: {str(e)}"},
            status_code=500
        )

@app.get("/bot/{bot_name}/settings")
async def get_bot_settings(bot_name: str):
    """Get settings for a specific bot."""
    try:
        if bot_name not in BOTS:
            return JSONResponse(
                content={"error": f"Bot '{bot_name}' not found"},
                status_code=404
            )

        bot_class = BOTS[bot_name]
        bot = bot_class()
        settings = await bot.get_settings() if hasattr(bot, 'get_settings') else {}
        
        return JSONResponse(content=settings)

    except Exception as e:
        logger.error(f"Error getting settings for bot {bot_name}: {str(e)}")
        return JSONResponse(
            content={"error": f"Error getting settings: {str(e)}"},
            status_code=500
        )

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Poe Bot Server")
    logger.info(f"Available bots: {sorted(list(BOTS.keys()))}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Poe Bot Server")