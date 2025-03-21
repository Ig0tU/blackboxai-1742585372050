"""
Sample bot that echoes back messages.

This is the simplest possible bot and a great place to start if you want to build your own bot.
"""

from __future__ import annotations

import os
from typing import AsyncIterable

import fastapi_poe as fp

# TODO: set your bot access key and bot name for full functionality
# see https://creator.poe.com/docs/quick-start#configuring-the-access-credentials
bot_access_key = os.getenv("POE_ACCESS_KEY")
bot_name = ""

class EchoBot(fp.PoeBot):
    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        last_message = request.query[-1].content
        yield fp.PartialResponse(text=last_message)
