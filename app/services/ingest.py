from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from app.core.ollama import embeddings
from app.db.sql_loader import load_data
from app.db.qdrant import client, COLLECTION_NAME

def ingest():
    df = load_data()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    texts = []
    metadatas = []

    for _, row in df.iterrows():
        chunks = splitter.split_text(row["Content"])

        for chunk in chunks:
            texts.append(chunk)
            metadatas.append({
                "id": row["Id"],
                "department": row["Department"]
            })

    vector_store = QdrantVectorStore.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
        url=client.url,
        collection_name=COLLECTION_NAME,
    )

    return "Ingest done"