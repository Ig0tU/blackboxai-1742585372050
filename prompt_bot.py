"""
Sample bot that demonstrates using a prompt template.
"""

from __future__ import annotations

from typing import AsyncIterable

import fastapi_poe as fp

PROMPT_TEMPLATE = """
You are a helpful assistant. Please respond to the following message:

{message}

Remember to be polite and professional.
"""

class PromptBot(fp.PoeBot):
    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        last_message = request.query[-1].content
        response = PROMPT_TEMPLATE.format(message=last_message)
        yield fp.PartialResponse(text=response)
