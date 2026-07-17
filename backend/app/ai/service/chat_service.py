import asyncio
from typing import cast

from app.ai.providers.llm.runtime import llm


class ChatService:
    async def chat(self, message: str) -> str:
        response = await asyncio.to_thread(llm.complete, message)

        return cast(str, response.text)
