from typing import Optional, List, Dict

from app.db.qdrant import get_qdrant_client
from app.core.ollama import embeddings, llm
from app.core.config import settings
from langchain_qdrant import QdrantVectorStore


def normalize_doc_id(doc_id: Optional[str]) -> Optional[str]:
    return doc_id.strip() if doc_id else None


def build_filter(doc_id: Optional[str] = None):
    must = []

    doc_id = normalize_doc_id(doc_id)
    if doc_id:
        must.append({
            "key": "doc_id",
            "match": {"value": doc_id}
        })

    return {"must": must} if must else None


def retrieve_docs(question: str, doc_id: Optional[str] = None):
    client = get_qdrant_client()

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=settings.QDRANT_COLLECTION,
        embedding=embeddings,
    )

    search_kwargs = {"k": 5}
    payload_filter = build_filter(doc_id)

    if payload_filter:
        search_kwargs["filter"] = payload_filter

    retriever = vector_store.as_retriever(search_kwargs=search_kwargs)
    docs = retriever.invoke(question)
    return docs


def fallback_keyword_docs(doc_id: Optional[str], question: str) -> List[Dict]:
    client = get_qdrant_client()
    question_terms = [t.lower() for t in question.split() if len(t) >= 3]

    payload_filter = build_filter(doc_id)

    points, _ = client.scroll(
        collection_name=settings.QDRANT_COLLECTION,
        scroll_filter=payload_filter,
        limit=50,
        with_payload=True,
        with_vectors=False,
    )

    matches = []
    for p in points:
        payload = p.payload or {}
        preview = (payload.get("text_preview") or "").lower()
        if any(term in preview for term in question_terms):
            matches.append(payload)

    return matches[:5]


def build_prompt(context: str, question: str) -> str:
    return f"""You are an assistant answering questions from OCR documents.

Rules:
- Answer only from the provided context.
- If the OCR is noisy or unclear, say that the OCR text is unclear.
- Do not make up facts.
- Keep the answer concise.
- If the answer cannot be found, say: I don't know based on the provided document.

Context:
{context}

Question:
{question}

Answer:
"""


def ask(question: str, doc_id: Optional[str] = None):
    docs = retrieve_docs(question, doc_id)

    if not docs:
        fallback = fallback_keyword_docs(doc_id, question)
        if not fallback:
            return {
                "answer": "No relevant data found.",
                "sources": []
            }

        context = "\n\n".join([f.get("text_preview", "") for f in fallback[:3]])
        result = llm.invoke(build_prompt(context, question))

        sources = []
        seen = set()
        for f in fallback:
            key = (f.get("doc_id"), f.get("page"))
            if key in seen:
                continue
            seen.add(key)
            sources.append({
                "doc_id": f.get("doc_id"),
                "page": f.get("page"),
            })

        return {
            "answer": result.content,
            "sources": sources,
        }

    context = "\n\n".join(doc.page_content for doc in docs[:4])
    result = llm.invoke(build_prompt(context, question))

    sources = []
    seen = set()
    for doc in docs:
        meta = doc.metadata or {}
        key = (meta.get("doc_id"), meta.get("page"))
        if key in seen:
            continue
        seen.add(key)
        sources.append({
            "doc_id": meta.get("doc_id"),
            "page": meta.get("page"),
        })

    return {
        "answer": result.content,
        "sources": sources,
    }