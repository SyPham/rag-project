import re
import hashlib
from typing import List, Dict

from qdrant_client.models import Distance, VectorParams
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.db.sql import get_connection
from app.db.qdrant import get_qdrant_client
from app.core.ollama import embeddings
from app.core.config import settings


def clean_ocr_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)

    # Giữ unicode chữ/số + vài dấu câu cơ bản
    text = re.sub(r"[^\w\sÀ-ỹ.,:;()/%\-]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def should_skip_chunk(text: str) -> bool:
    if not text:
        return True
    if len(text) < 80:
        return True
    # chunk quá nghèo thông tin
    alnum_count = sum(ch.isalnum() for ch in text)
    return alnum_count < 30


def make_point_id(ocr_id: str, chunk_index: int) -> str:
    raw = f"{ocr_id}_{chunk_index}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def get_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=80,
        separators=["\n\n", "\n", ". ", "; ", ", ", " "],
    )


def fetch_ocr_rows(limit: int | None = None) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    SELECT
        Id,
        DocumentId,
        PageNumber,
        Content,
        OCRSyncLogId,
        CreationTime,
        TaskList
    FROM OCRDocuments
    WHERE Content IS NOT NULL
      AND LTRIM(RTRIM(Content)) <> ''
    ORDER BY DocumentId, PageNumber
    """

    if limit:
        sql = f"""
        SELECT TOP ({limit})
            Id,
            DocumentId,
            PageNumber,
            Content,
            OCRSyncLogId,
            CreationTime,
            TaskList
        FROM OCRDocuments
        WHERE Content IS NOT NULL
          AND LTRIM(RTRIM(Content)) <> ''
        ORDER BY DocumentId, PageNumber
        """

    rows = cursor.execute(sql).fetchall()

    result = []
    for row in rows:
        result.append({
            "ocr_id": str(row.Id),
            "doc_id": str(row.DocumentId),
            "page": int(row.PageNumber),
            "content": row.Content or "",
            "ocr_sync_log_id": str(row.OCRSyncLogId),
            "created_at": row.CreationTime.isoformat() if row.CreationTime else None,
            "task_list": row.TaskList,
        })
    return result


def ensure_collection(vector_size: int):
    client = get_qdrant_client()
    collection_name = settings.QDRANT_COLLECTION

    collections = client.get_collections().collections
    exists = any(c.name == collection_name for c in collections)

    if not exists:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )


def ingest_ocr(limit: int | None = None):
    rows = fetch_ocr_rows(limit=limit)
    if not rows:
        return {"message": "No OCR rows found.", "points": 0}

    splitter = get_splitter()

    texts: List[str] = []
    metadatas: List[Dict] = []
    ids: List[str] = []

    for row in rows:
        cleaned = clean_ocr_text(row["content"])
        if not cleaned:
            continue

        chunks = splitter.split_text(cleaned)

        chunk_index = 0
        for chunk in chunks:
            chunk = chunk.strip()
            if should_skip_chunk(chunk):
                continue

            texts.append(chunk)
            metadatas.append({
                "ocr_id": row["ocr_id"],
                "doc_id": row["doc_id"],
                "page": row["page"],
                "chunk_index": chunk_index,
                "ocr_sync_log_id": row["ocr_sync_log_id"],
                "created_at": row["created_at"],
                "task_list": row["task_list"],
                "text_preview": chunk[:200],
            })
            ids.append(make_point_id(row["ocr_id"], chunk_index))
            chunk_index += 1

    if not texts:
        return {"message": "No valid chunks after cleaning.", "points": 0}

    # Lấy vector size thật từ model đang dùng
    sample_vector = embeddings.embed_query("test")
    vector_size = len(sample_vector)

    ensure_collection(vector_size)

    from langchain_qdrant import QdrantVectorStore

    client = get_qdrant_client()

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=settings.QDRANT_COLLECTION,
        embedding=embeddings,
    )

    vector_store.add_texts(
        texts=texts,
        metadatas=metadatas,
        ids=ids,
    )

    return {
        "message": "OCR ingestion completed.",
        "points": len(texts),
        "documents": len(set(m["doc_id"] for m in metadatas)),
    }