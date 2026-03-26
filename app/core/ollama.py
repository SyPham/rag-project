from langchain_ollama import ChatOllama, OllamaEmbeddings
from app.core.config import settings

llm = ChatOllama(
    model=settings.OLLAMA_LLM,
    base_url=settings.OLLAMA_BASE_URL,
)

embeddings = OllamaEmbeddings(
    model=settings.OLLAMA_EMBED,
    base_url=settings.OLLAMA_BASE_URL,
)