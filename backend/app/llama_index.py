from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from app.config import settings


def configure_llama_index() -> None:
    Settings.llm = OpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        api_base=settings.OPENAI_BASE_URL,  # or base_url depending on your version
        temperature=0,
    )

    Settings.embed_model = OpenAIEmbedding(
        model=settings.OPENAI_EMBEDDING_MODEL,
        api_key=settings.OPENAI_API_KEY,
        api_base=settings.OPENAI_BASE_URL,
    )
 
    Settings.chunk_size = 1024
    Settings.chunk_overlap = 100

    Settings.context_window = 8192
    Settings.num_output = 512