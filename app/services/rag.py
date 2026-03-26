from qdrant_client import QdrantClient
from app.core.ollama import embeddings, llm
from langchain_qdrant import QdrantVectorStore
import os

QDRANT_URL = os.getenv("QDRANT_URL")
COLLECTION = os.getenv("QDRANT_COLLECTION")


def build_filter(doc_id=None, department=None):
    must = []

    if doc_id:
        must.append({
            "key": "doc_id",
            "match": {"value": doc_id}
        })

    if department:
        must.append({
            "key": "department",
            "match": {"value": department}
        })

    return {"must": must} if must else None


def retrieve_docs(question, doc_id=None, department=None):
    from qdrant_client import QdrantClient

    client = QdrantClient(url=QDRANT_URL)

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION,
        embedding=embeddings
    )

    retriever = vector_store.as_retriever(
        search_kwargs={
            "k": 5,
            "filter": build_filter(doc_id, department)
        }
    )

    docs = retriever.invoke(question)

    return docs

def build_prompt(context, question):
    return f"""
You are an AI assistant.

Answer ONLY based on the context below.
If the answer is not in the context, say "I don't know".

Context:
{context}

Question:
{question}

Answer:
"""


def ask(question, doc_id=None, department=None):
    docs = retrieve_docs(question, doc_id, department)

    if not docs:
        return {
            "answer": "No relevant data found.",
            "sources": []
        }

    context = "\n\n".join([doc.page_content for doc in docs])

    prompt = build_prompt(context, question)

    result = llm.invoke(prompt)

    sources = []
    seen = set()

    for doc in docs:
        key = (doc.metadata["doc_id"], doc.metadata["page"])
        if key not in seen:
            seen.add(key)
            sources.append({
                "doc_id": doc.metadata["doc_id"],
                "page": doc.metadata["page"]
            })

    return {
        "answer": result.content,
        "sources": sources
    }