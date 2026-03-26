from app.db.sql import get_connection
from app.core.ollama import embeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import os
from uuid import uuid4
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
COLLECTION = os.getenv("QDRANT_COLLECTION")
print("QDRANT_URL:", QDRANT_URL)
print("COLLECTION:", COLLECTION)
print("SQL_CONNECTION:", os.getenv("SQL_CONNECTION")[:50])

def clean_ocr_text(text: str):
    return " ".join(text.replace("\n", " ").split())


def ingest_ocr(batch_size=100):
    print("🚀 Start ingest OCR...")

    # 1. DB connection
    conn = get_connection()
    cursor = conn.cursor()
    print("✅ Connected to DB")

    # 2. Query
    query = """
    SELECT Id, DocumentId, PageNumber, Content, CreationTime
    FROM OCRDocuments
    WHERE Content IS NOT NULL
    """
    cursor.execute(query)
    print("✅ Query executed")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
    )

    client = QdrantClient(url=QDRANT_URL)

    # 3. Check/Create collection
    collections = [c.name for c in client.get_collections().collections]
    print(f"📦 Existing collections: {collections}")

    if COLLECTION not in collections:
        print(f"⚠️ Collection '{COLLECTION}' not found → creating...")
        from qdrant_client.models import Distance, VectorParams
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
        print("✅ Collection created")

    # 4. Init vector store
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION,
        embedding=embeddings,
    )
    print("✅ Vector store ready")

    texts, metadatas, ids = [], [], []
    row_count = 0
    chunk_count = 0

    # 5. Loop data
    for row in cursor:
        row_count += 1

        if row_count % 50 == 0:
            print(f"📄 Processed rows: {row_count}")

        content = clean_ocr_text(row.Content)

        if not content:
            print(f"⚠️ Empty content at row {row.Id}")
            continue

        chunks = splitter.split_text(content)

        print(f"🔹 Row {row.Id} → {len(chunks)} chunks")

        for idx, chunk in enumerate(chunks):
            texts.append(chunk)

            metadatas.append({
                "ocr_id": str(row.Id),
                "doc_id": str(row.DocumentId),
                "page": row.PageNumber,
                "chunk_index": idx,
                "created_at": str(row.CreationTime)
            })

            
            ids.append(str(uuid4()))

            chunk_count += 1

        # 6. Batch insert
        if row_count % batch_size == 0:
            print(f"📤 Inserting batch: {len(texts)} chunks")

            vector_store.add_texts(
                texts=texts,
                metadatas=metadatas,
                ids=ids,
            )

            print("✅ Batch inserted")

            texts, metadatas, ids = [], [], []

    # 7. Insert remaining
    if texts:
        print(f"📤 Final insert: {len(texts)} chunks")

        vector_store.add_texts(
            texts=texts,
            metadatas=metadatas,
            ids=ids,
        )

        print("✅ Final batch inserted")

    # 8. Final check
    info = client.get_collection(COLLECTION)
    print(f"📊 Total vectors in Qdrant: {info.points_count}")

    print("🎉 Ingest OCR DONE!")

    return "Ingest OCR done"
if __name__ == "__main__":
    ingest_ocr()