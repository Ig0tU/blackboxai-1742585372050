"""
Enterprise Wrapper Bot that uses Poe's API to interact with high-end models like GPT-4 and Claude.
"""

from __future__ import annotations

import os
import json
import logging
import asyncio
from typing import AsyncIterable, Dict, Any
from enum import Enum

import fastapi_poe as fp
import httpx

logger = logging.getLogger(__name__)

class ModelType(Enum):
    GPT4 = "GPT-4"
    CLAUDE = "Claude-3-Opus"

class EnterpriseWrapperBot(fp.PoeBot):
    def __init__(self):
        super().__init__()
        self.poe_token_b = os.getenv("POE_TOKEN_B", "")
        self.poe_token_lat = os.getenv("POE_TOKEN_LAT", "")
        self.default_model = ModelType.GPT4
        
        # Initialize HTTP client
        self.http_client = httpx.AsyncClient(timeout=60.0)

    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        try:
            # Extract the last message and any settings
            last_message = request.query[-1].content
            settings = self._parse_settings(last_message)
            
            # Get conversation history
            history = self._format_conversation_history(request.query)
            
            # Choose the model based on settings or default
            model = settings.get("model", self.default_model)
            
            # Call Poe API
            response = await self._call_poe_api(history, model)
            
            # Stream the response
            for chunk in response.split():  # Split into words for streaming effect
                yield fp.PartialResponse(text=chunk + " ")
                await asyncio.sleep(0.05)  # Add slight delay between words

        except Exception as e:
            logger.error(f"Error in get_response: {str(e)}")
            yield fp.PartialResponse(
                text=f"An error occurred while processing your request: {str(e)}"
            )

    def _parse_settings(self, message: str) -> Dict[str, Any]:
        """Extract settings from message if present."""
        settings = {
            "model": self.default_model
        }
        
        # Check for settings in JSON format at the start of the message
        if message.startswith("{") and "}" in message:
            try:
                settings_end = message.index("}") + 1
                settings_str = message[:settings_end]
                user_settings = json.loads(settings_str)
                settings.update(user_settings)
                
                # Convert model string to enum
                if "model" in user_settings:
                    settings["model"] = ModelType(user_settings["model"])
            except:
                pass
                
        return settings

    def _format_conversation_history(self, messages: list) -> list:
        """Format conversation history for Poe API."""
        formatted = []
        for msg in messages:
            formatted.append({
                "role": "assistant" if msg.role == "bot" else "user",
                "content": msg.content
            })
        return formatted

    async def _call_poe_api(self, history: list, model: ModelType) -> str:
        """Call Poe API using tokens."""
        if not self.poe_token_b or not self.poe_token_lat:
            return "Poe tokens not configured. Please set POE_TOKEN_B and POE_TOKEN_LAT environment variables."
            
        try:
            # Construct the message from history
            message = history[-1]["content"] if history else ""
            
            # Map model type to Poe bot handle
            model_map = {
                ModelType.GPT4: "GPT-4",
                ModelType.CLAUDE: "Claude-3-Opus"
            }
            
            bot_handle = model_map.get(model, model_map[ModelType.GPT4])
            
            # Headers for authentication
            headers = {
                "Cookie": f"p-b={self.poe_token_b}; p-lat={self.poe_token_lat}",
                "User-Agent": "Mozilla/5.0",
                "Content-Type": "application/json"
            }
            
            # Make POST request to Poe's GraphQL endpoint
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://poe.com/api/gql_POST",
                    headers=headers,
                    json={
                        "queryName": "ChatHelpers_sendMessageMutation_Mutation",
                        "variables": {
                            "bot": bot_handle,
                            "message": message,
                            "conversationId": None,
                            "source": None,
                            "withChatBreak": False
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Extract the bot's response from the GraphQL response
                    text = data.get("data", {}).get("messageResponse", {}).get("text", "")
                    if not text:
                        text = "Could not parse response from Poe API"
                    return text
                else:
                    return f"Error from Poe API: {response.text}"
                    
        except Exception as e:
            logger.error(f"Error calling Poe API: {str(e)}")
            return f"Error calling Poe API: {str(e)}"

    async def on_error(self, error: Exception) -> fp.ErrorResponse:
        """Handle errors gracefully."""
        logger.error(f"Bot error: {str(error)}")
        return fp.ErrorResponse(
            text="I apologize, but an error occurred while processing your request. "
                 "Please try again or contact support if the issue persists."
        )