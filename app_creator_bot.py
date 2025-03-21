"""
Simple bot that forwards requests to Poe's App Creator.
"""

import fastapi_poe as fp
from typing import AsyncIterable

class AppCreatorBot(fp.PoeBot):
    async def get_response(self, request: fp.QueryRequest) -> AsyncIterable[fp.PartialResponse]:
        message = request.query[-1].content
        async for chunk in fp.get_bot_response("App-Creator", message):
            yield fp.PartialResponse(text=chunk)

if __name__ == "__main__":
    fp.run(AppCreatorBot(), access_key="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")