from fastapi import FastAPI
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag import ask
from app.services.ingest_ocr import ingest_ocr

app = FastAPI(title="OCR RAG API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
def ingest(limit: int | None = None):
    return ingest_ocr(limit=limit)


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    return ask(question=req.question, doc_id=req.doc_id)