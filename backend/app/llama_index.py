from llama_index.llms.openai_like import OpenAILike

from app.config import settings

llm = OpenAILike(
    model=settings.LLM_MODEL,
    api_base=settings.LLM_BASE_URL,
    api_key=settings.LLM_API_KEY,
    context_window=128000,
    is_chat_model=True,
    is_function_calling_model=False,
)