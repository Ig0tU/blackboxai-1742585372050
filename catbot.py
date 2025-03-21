"""
Sample bot that demonstrates handling different types of responses about cats.
"""

from __future__ import annotations

from typing import AsyncIterable
import random

import fastapi_poe as fp

CAT_FACTS = [
    "Cats spend 70% of their lives sleeping.",
    "A cat's nose print is unique, much like a human's fingerprint.",
    "Cats have 32 muscles in each ear.",
    "A group of cats is called a clowder.",
    "Cats can't taste sweetness.",
    "A cat can jump up to six times its length.",
]

CAT_RESPONSES = [
    "Meow! 🐱",
    "Purrrr... 😺",
    "Mrrrow! 😸",
    "*stretches and yawns* 😽",
    "*rubs against your leg* 😺",
]

class CatBot(fp.PoeBot):
    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        last_message = request.query[-1].content.lower()
        
        if "fact" in last_message:
            response = f"Here's a cat fact: {random.choice(CAT_FACTS)}"
        else:
            response = random.choice(CAT_RESPONSES)
        
        yield fp.PartialResponse(text=response)
