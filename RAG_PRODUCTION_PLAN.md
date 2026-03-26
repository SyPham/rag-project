# 🚀 RAG PRODUCTION PLAN (OCR + Qdrant + Ollama)

## 🎯 Mục tiêu
Xây dựng hệ thống RAG production:
- Query dữ liệu từ OCRDocuments (SQL Server)
- Lưu vector vào Qdrant
- Hỗ trợ hỏi đáp theo tài liệu (có phân quyền doc_id)
- Tối ưu cho OCR noisy data

---

# 🏗️ 1. Kiến trúc tổng thể


SQL Server (OCRDocuments)
↓
[Ingestion Pipeline]
↓
Clean OCR → Chunk → Embedding
↓
Qdrant (Vector DB)
↓
[Retrieval Layer]
Dense + Sparse + Rerank
↓
[LLM - Ollama]
↓
FastAPI (/chat)
↓
Console / UI


---

# 🔄 2. Data Ingestion Pipeline

## 2.1 Nguồn dữ liệu
- Table: OCRDocuments
- Fields:
  - DocumentId → doc_id
  - PageNumber → page
  - Content → text OCR

---

## 2.2 Clean OCR (BẮT BUỘC)

### Vấn đề:
- OCR noise
- ký tự rác
- sai chính tả

### Giải pháp:

```python
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9À-ỹ\s.,-]', ' ', text)
    return text.strip()
2.3 Chunking Strategy
❌ Sai:
1 page = 1 chunk
✅ Đúng:
chunk_size = 400-500
chunk_overlap = 80-100
Output:
chunk nhỏ → tăng recall
dễ match embedding
2.4 Metadata chuẩn
{
  "doc_id": "...",
  "page": 1,
  "ocr_id": "...",
  "chunk_index": 0,
  "created_at": "...",
  "text_preview": "..."
}
2.5 Embedding
Model:
embeddinggemma
qwen3-embedding (recommended)
2.6 Upsert Qdrant
distance: COSINE
vector size: auto detect
🔍 3. Retrieval Layer (CORE)
3.1 Flow chuẩn
User Query
  ↓
Normalize Query
  ↓
Dense Search (top 20)
  ↓
Sparse Search (top 20)
  ↓
Fusion
  ↓
Rerank (top 5)
  ↓
Context build
3.2 Dense Search
vector_store.as_retriever(k=20)
3.3 Sparse Search (fallback cực quan trọng)
keyword match
OCR-friendly
3.4 Fusion

Combine:

dense score
keyword match
3.5 Rerank
lọc top 20 → top 5
giảm noise
🤖 4. LLM Answer Layer
Prompt chuẩn
Rules:
- Only use provided context
- If OCR unclear → say unclear
- Do not hallucinate
- Answer concise
Context build
context = "\n\n".join(top_chunks)
Output
{
  "answer": "...",
  "sources": [
    { "doc_id": "...", "page": 1 }
  ]
}
🌐 5. API Layer (FastAPI)
Endpoints
1. Ingest
POST /ingest
2. Chat
POST /chat
3. Health
GET /health
Request
{
  "question": "...",
  "doc_id": "..."
}
💬 6. Query Strategy (RẤT QUAN TRỌNG)
✅ Nên hỏi
"liệt kê tên"
"diện tích của Nguyễn Văn A"
"ai có diện tích lớn nhất"
❌ Không nên hỏi
"tài liệu này nói gì"
"tóm tắt tài liệu"
👉 Quy tắc
Loại	Cách hỏi
Extract	list / liệt kê
Filter	ai có / những người
Compare	so sánh
Aggregate	tổng / lớn nhất
🧪 7. Testing Strategy
Test cases
Level 1
list names
Level 2
diện tích của A
Level 3
ai lớn nhất
Level 4
cross page
Debug
print(context)
print(docs)
📈 8. Production Improvements
8.1 Hybrid Search
dense + BM25
8.2 Reranking
cross encoder
8.3 Query Rewrite
"tóm tắt tài liệu"
→ "liệt kê dữ liệu chính"
8.4 Incremental Sync
chỉ ingest dữ liệu mới
8.5 Logging

Log:

request_id
question
retrieved docs
latency
8.6 Streaming
/chat/stream
⚠️ 9. Known Issues
Issue	Solution
OCR noise	clean + chunk
query generic	rewrite
no result	fallback keyword
wrong answer	rerank
🚀 10. Roadmap
Phase 1
clean OCR
chunk đúng
basic RAG
Phase 2
hybrid search
fallback
Phase 3
rerank
streaming
logging
🔥 11. Kết luận

Để RAG chạy tốt với OCR:

👉 80% success = clean + chunk
👉 20% = model + prompt

🎯 NEXT STEP
 Implement ingestion pipeline
 Fix chunking
 Add fallback search
 Test with sample data
 Add reranking
 Optimize query