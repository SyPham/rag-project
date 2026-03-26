from fastapi import FastAPI
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag import ask

app = FastAPI()


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = ask(
        question=req.question,
        doc_id=req.doc_id,
        department=req.department
    )

    return result