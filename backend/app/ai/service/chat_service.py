import asyncio

from llama_index.core import Settings


class ChatService:

    async def chat(self, message: str) -> str:
        if Settings.llm is None:
            raise RuntimeError("LLM is not configured. Check startup initialization.")

        response = await asyncio.to_thread(Settings.llm.complete, message)

        return response.text