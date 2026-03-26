from qdrant_client import QdrantClient
import os

client = QdrantClient(
    url=os.getenv("QDRANT_URL")
)

COLLECTION_NAME = os.getenv("QDRANT_COLLECTION")