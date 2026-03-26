`pdm run python app/main.py`
rag-chatbot/
│
├── app/
│   ├── main.py              # FastAPI entry
│   ├── core/
│   │   ├── config.py
│   │   └── ollama.py
│   │
│   ├── db/
│   │   ├── sql_loader.py    # load từ SQL
│   │   └── qdrant.py        # connect Qdrant
│   │
│   ├── services/
│   │   ├── ingest.py        # sync SQL -> Qdrant
│   │   └── rag.py           # hỏi đáp
│   │
│   └── schemas/
│       └── chat.py
│
├── .env
├── pyproject.toml
└── README.md

# How to run the project?
`pdm run python -m app.services.ingest_ocr`
`pdm run uvicorn app.main:app --reload`

User question
   ↓
Embed query
   ↓
Search Qdrant (filter)
   ↓
Lấy top K chunks
   ↓
Build prompt (context + question)
   ↓
Ollama generate
   ↓
Return answer + sources