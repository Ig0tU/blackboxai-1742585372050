"""
Sample bot that demonstrates logging functionality.
"""

from __future__ import annotations

import logging
from typing import AsyncIterable

import fastapi_poe as fp

logger = logging.getLogger(__name__)

class LogBot(fp.PoeBot):
    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        last_message = request.query[-1].content
        
        # Log the incoming message
        logger.info(f"Received message: {last_message}")
        
        # Create and log the response
        response = f"I received your message and logged it: {last_message}"
        logger.info(f"Sending response: {response}")
        
        yield fp.PartialResponse(text=response)
