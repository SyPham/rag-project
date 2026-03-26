from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
    OLLAMA_LLM = os.getenv("OLLAMA_LLM")
    OLLAMA_EMBED = os.getenv("OLLAMA_EMBED")

    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION")
    
settings = Settings()