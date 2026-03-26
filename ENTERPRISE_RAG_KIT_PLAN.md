# Enterprise RAG Kit Plan

## 1. Mục tiêu
Xây dựng một bộ RAG production-ready cho dữ liệu OCR, chạy local bằng Ollama, dùng SQL Server làm nguồn dữ liệu gốc, Qdrant làm vector database, FastAPI làm API layer, và có phân quyền dữ liệu ngay tại tầng retrieval.

Mục tiêu chính:
- Đồng bộ dữ liệu từ `OCRDocuments` sang Qdrant ổn định và có thể chạy lại nhiều lần.
- Tối ưu cho OCR noisy text.
- Hỗ trợ hỏi đáp theo từng tài liệu hoặc toàn bộ kho tài liệu.
- Chặn truy xuất trái phép bằng metadata filter ở Qdrant.
- Có logging, audit, tracing, streaming, fallback retrieval, và plan mở rộng enterprise.

---

## 2. Kiến trúc tổng thể

```text
SQL Server (OCRDocuments)
        ↓
Ingestion Worker
        ↓
Clean OCR → Chunk → Embed
        ↓
Qdrant
        ↓
Retrieval Layer
(Dense + Keyword fallback + optional rerank)
        ↓
Authorization Filter
(doc scope + role scope + tenant scope + sensitivity scope)
        ↓
LLM Layer (Ollama)
        ↓
FastAPI
        ↓
Console / Web UI / Internal API consumers
```

### Thành phần
- **SQL Server**: source of truth.
- **Ingestion Worker**: đọc SQL, làm sạch OCR, chunk, embed, upsert vào Qdrant.
- **Qdrant**: lưu vectors + payload metadata.
- **Retrieval Layer**: truy xuất ngữ nghĩa, keyword fallback, fusion.
- **Authorization Layer**: thêm điều kiện filter theo quyền trước khi query vector DB.
- **LLM Layer**: sinh câu trả lời chỉ từ context.
- **FastAPI**: phơi bày `/ingest`, `/chat`, `/chat/stream`, `/health`.

---

## 3. Cấu trúc thư mục đề xuất

```text
rag-project/
├── app/
│   ├── api/
│   │   └── deps.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── logging.py
│   │   └── ollama.py
│   ├── db/
│   │   ├── sql.py
│   │   └── qdrant.py
│   ├── models/
│   │   └── auth.py
│   ├── schemas/
│   │   ├── chat.py
│   │   └── ingest.py
│   ├── services/
│   │   ├── ingest_ocr.py
│   │   ├── retrieval.py
│   │   ├── authorization.py
│   │   ├── rag.py
│   │   └── audit.py
│   ├── workers/
│   │   └── ingest_runner.py
│   ├── main.py
│   └── chat_console.py
├── tests/
├── .env
├── pyproject.toml
└── ENTERPRISE_RAG_KIT_PLAN.md
```

---

## 4. Dữ liệu nguồn: OCRDocuments

### Bảng nguồn
- `Id`
- `PageNumber`
- `DocumentId`
- `Content`
- `OCRSyncLogId`
- `CreationTime`
- `TaskList`

### Mapping sang payload Qdrant

```json
{
  "ocr_id": "Id",
  "doc_id": "DocumentId",
  "page": 1,
  "chunk_index": 0,
  "ocr_sync_log_id": "OCRSyncLogId",
  "created_at": "CreationTime",
  "task_list": "TaskList",
  "text_preview": "first 200 chars",
  "tenant_id": "optional",
  "department": "optional",
  "allowed_roles": ["Admin", "LegalReader"],
  "allowed_users": ["user-guid-1"],
  "sensitivity": "public|internal|confidential|secret",
  "source_table": "OCRDocuments"
}
```

---

## 5. Ingestion pipeline chuẩn enterprise

## 5.1 Mục tiêu ingestion
- Không duplicate.
- Có thể chạy incremental.
- Có thể reindex một document riêng.
- Có thể bỏ qua row quá bẩn hoặc quá ngắn.

## 5.2 Các bước
1. Kết nối SQL Server.
2. Đọc bản ghi OCR có `Content` hợp lệ.
3. Clean OCR text.
4. Chunk text.
5. Sinh embedding bằng Ollama.
6. Upsert vào Qdrant.
7. Log số lượng thành công/thất bại.

## 5.3 Clean OCR
Với OCR noisy, cần:
- chuẩn hóa khoảng trắng
- bỏ control characters
- giữ chữ cái tiếng Việt, chữ số, dấu câu cơ bản
- loại chunk quá ngắn

Pseudo-code:

```python
def clean_ocr_text(text: str) -> str:
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\sÀ-ỹ.,:;()/%\-]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text
```

## 5.4 Chunking strategy
Với OCR, không nên để 1 page = 1 chunk.

Khuyến nghị:
- `chunk_size`: 350–500 ký tự
- `chunk_overlap`: 60–100 ký tự
- separators: `\n\n`, `\n`, `. `, `; `, `, `, ` `

Mục tiêu:
- tăng recall
- giảm việc mỗi chunk chứa quá nhiều noise
- tạo nhiều điểm neo cho retrieval

## 5.5 Bỏ chunk xấu
Ví dụ bỏ:
- chunk ngắn dưới 80 ký tự
- chunk có quá ít ký tự chữ/số
- chunk chỉ chứa mã vô nghĩa

## 5.6 ID chiến lược
Dùng deterministic ID để tránh duplicate:

```text
md5(ocr_id + '_' + chunk_index)
```

Nhờ vậy có thể re-run ingestion mà không tạo trùng.

## 5.7 Incremental sync
Khuyến nghị thêm cột watermark theo:
- `CreationTime`
- hoặc `LastModificationTime` nếu có

Chiến lược:
- lưu `last_sync_at` trong bảng hệ thống hoặc file state
- lần sau chỉ ingest bản ghi mới hơn mốc đó

---

## 6. Qdrant design

## 6.1 Collection
- `documents`

## 6.2 Distance metric
- `COSINE`

## 6.3 Payload indexes
Cần tạo index cho các field filter thường dùng, vì Qdrant hỗ trợ filtering và payload indexing cho hiệu năng tốt hơn, nhất là với payload fields dùng trong search filters. citeturn962842search1turn962842search5turn962842search21

Index nên có:
- `doc_id`
- `tenant_id`
- `department`
- `sensitivity`
- `page`
- `allowed_users`
- `allowed_roles`

## 6.4 Quy ước collection tách riêng
Nếu hệ thống lớn, có thể cân nhắc 2 mode:
- **Shared collection + metadata filter**
- **Collection per tenant**

Khuyến nghị ban đầu:
- shared collection nếu số tenant vừa phải
- tách collection riêng nếu tenant có dữ liệu lớn và yêu cầu cô lập mạnh

---

## 7. Retrieval layer production

## 7.1 Chuỗi truy vấn

```text
User Query
→ normalize query
→ build authorization filter
→ dense retrieval top 20
→ keyword fallback / sparse-like retrieval top 20
→ fusion
→ optional rerank top 5
→ build context
→ LLM answer
```

## 7.2 Normalize query
- strip whitespace
- collapse multiple spaces
- lowercase cho keyword fallback
- giữ nguyên bản gốc để đưa vào prompt

## 7.3 Dense retrieval
LangChain tích hợp Qdrant vector store để thêm documents, similarity search, và metadata filtering. citeturn962842search0turn962842search12

## 7.4 Keyword fallback
Với OCR, dense retrieval dễ hụt nếu query chứa:
- tên riêng
- mã hồ sơ
- số thửa
- số tiền
- ngày tháng

Do đó cần keyword fallback trên `text_preview` hoặc raw chunk.

## 7.5 Fusion
Cách đơn giản:
- gộp dense hits + keyword hits
- loại trùng theo `(doc_id, page, chunk_index)`
- ưu tiên item xuất hiện ở cả 2 nguồn

## 7.6 Rerank
Phase đầu có thể rerank rule-based:
- nhiều token trùng query hơn → score cao hơn
- cùng `doc_id` được yêu cầu → boost
- page gần nhau → boost nhẹ

Phase sau mới thay bằng cross-encoder.

---

## 8. Authorization / phân quyền dữ liệu

Đây là phần bạn muốn thêm, và nên áp dụng ở **retrieval time**, không chờ tới sau khi đã lấy context.

## 8.1 Mục tiêu
Người dùng chỉ được retrieve những chunk họ có quyền xem.

## 8.2 Metadata quyền đề xuất
Payload mỗi chunk nên có thêm:

```json
{
  "tenant_id": "tenant-a",
  "department": "Legal",
  "allowed_roles": ["Admin", "LegalReader"],
  "allowed_users": ["8f...", "3a..."],
  "sensitivity": "confidential"
}
```

## 8.3 Nguồn quyền có thể lấy từ đâu
- JWT claims
- user profile DB
- RBAC table trong SQL Server
- mapping document ownership table

## 8.4 Mô hình quyền đề xuất
### Cấp 1: Tenant scope
- user chỉ thấy dữ liệu tenant của mình

### Cấp 2: Department scope
- user chỉ thấy tài liệu thuộc phòng ban của họ nếu không có quyền cross-department

### Cấp 3: Role scope
- role quyết định loại sensitivity được xem

### Cấp 4: User override
- `allowed_users` cho phép chia sẻ riêng từng document

## 8.5 Sensitivity matrix đề xuất

| sensitivity | viewer roles |
|---|---|
| public | mọi user hợp lệ |
| internal | nội bộ tenant |
| confidential | role chuyên trách |
| secret | admin hoặc explicit allow |

## 8.6 Filter builder
Qdrant hỗ trợ payload filtering để đặt điều kiện trên dữ liệu ngoài vector, rất phù hợp cho business rules như phân quyền, vị trí, giá, hoặc availability. citeturn962842search1turn962842search17

Pseudo-code:

```python
def build_auth_filter(user_ctx, doc_id=None):
    must = []
    should = []

    must.append({"key": "tenant_id", "match": {"value": user_ctx.tenant_id}})

    if doc_id:
        must.append({"key": "doc_id", "match": {"value": doc_id}})

    # sensitivity gate
    allowed_sensitivity = user_ctx.allowed_sensitivity
    should.append({"key": "sensitivity", "match": {"value": "public"}})
    for s in allowed_sensitivity:
        should.append({"key": "sensitivity", "match": {"value": s}})

    # direct user grant
    should.append({"key": "allowed_users", "match": {"value": user_ctx.user_id}})

    # role grant
    for role in user_ctx.roles:
        should.append({"key": "allowed_roles", "match": {"value": role}})

    return {
        "must": must,
        "should": should,
        "minimum_should_match": 1,
    }
```

## 8.7 Nguyên tắc bắt buộc
- Không retrieve rồi mới lọc bằng Python nếu dữ liệu nhạy cảm.
- Phải filter ngay trong Qdrant query.
- Mọi log audit phải ghi rõ user nào hỏi, doc scope nào, nguồn nào được trả về.

## 8.8 Audit for authorization
Mỗi request cần log:
- `request_id`
- `user_id`
- `tenant_id`
- `roles`
- `doc_id` yêu cầu
- number of retrieved chunks
- sources pages
- blocked/allowed status

---

## 9. API layer enterprise

## 9.1 Endpoints
- `GET /health`
- `POST /ingest`
- `POST /chat`
- `POST /chat/stream`
- `POST /reindex/document/{doc_id}`
- `GET /audit/{request_id}`

## 9.2 `/chat`
Request:

```json
{
  "question": "liệt kê tên trong tài liệu",
  "doc_id": "GUID_OPTIONAL"
}
```

Response:

```json
{
  "request_id": "uuid",
  "answer": "...",
  "sources": [
    {"doc_id": "...", "page": 1},
    {"doc_id": "...", "page": 2}
  ],
  "meta": {
    "retrieved_chunks": 5,
    "retrieval_mode": "dense+keyword",
    "authorized": true
  }
}
```

## 9.3 `/chat/stream`
FastAPI hỗ trợ `StreamingResponse` để stream từng phần dữ liệu thay vì chờ xong toàn bộ response. citeturn962842search14turn962842search2turn962842search6

Dùng cho:
- console chat thời gian thực
- web UI kiểu ChatGPT

## 9.4 `/ingest`
Mode:
- full ingest
- incremental ingest
- by document id

---

## 10. LLM layer

## 10.1 Ollama
Ollama chạy API local mặc định tại `http://localhost:11434/api`, và có endpoint `/api/embed` cho embeddings. Recommended embedding models gồm `embeddinggemma`, `qwen3-embedding`, `all-minilm`. citeturn962842search11turn962842search7turn962842search3turn962842search24

## 10.2 Model đề xuất
- Chat: `qwen2.5` hoặc model local bạn đang dùng ổn định
- Embedding: `qwen3-embedding` hoặc `embeddinggemma`

## 10.3 Prompt policy
Prompt cần ép chặt:
- chỉ dùng context
- nếu OCR unclear thì nói rõ unclear
- không đoán bừa
- trả lời ngắn, factual
- giữ nguyên số liệu, tên riêng nếu có thể

Pseudo:

```text
You answer questions from OCR documents.
Rules:
- Use only provided context.
- If OCR text is noisy or unclear, say so.
- Do not make up facts.
- Return concise answers.
```

---

## 11. Console / UI kit

## 11.1 Console
Tính năng nên có:
- nhập `doc_id`
- hỏi nhiều lượt
- in raw status code
- hiện sources
- hiện request_id

## 11.2 Web UI
Tối thiểu:
- ô nhập câu hỏi
- ô nhập `doc_id`
- panel hiển thị sources
- panel hiển thị pages liên quan
- loader / streaming token

---

## 12. Logging, tracing, monitoring

## 12.1 Structured logging
Log dạng JSON cho từng request:
- request_id
- user_id
- tenant_id
- question
- doc_id
- latency_ms
- retrieved_chunks
- source_pages
- llm_model
- embedding_model

## 12.2 Latency breakdown
Nên log:
- SQL fetch time
- embedding time
- Qdrant retrieval time
- rerank time
- LLM generation time

## 12.3 Error categories
- SQL connection error
- embedding error
- Qdrant error
- authorization denied
- LLM timeout
- malformed OCR

---

## 13. Security controls

## 13.1 API auth
- JWT bearer token
- parse claims thành `UserContext`

## 13.2 Secrets
- `.env` cho local
- production dùng secret manager

## 13.3 Network
- Qdrant không expose public nếu không cần
- Ollama chỉ expose nội bộ

## 13.4 Prompt injection mitigation
- không đưa raw user instruction trực tiếp vào system prompt
- không cho model tự do truy vấn ngoài sources đã retrieve

---

## 14. Testing kit

## 14.1 Unit tests
- clean text
- chunking
- auth filter builder
- deterministic point id

## 14.2 Integration tests
- ingest SQL → Qdrant
- `/chat` với doc cụ thể
- `/chat` với user không có quyền
- `/chat` với fallback keyword

## 14.3 Evaluation dataset
Tạo bộ câu hỏi chuẩn:
- extract tên
- extract số tiền
- extract số thửa
- so sánh 2 người
- tổng hợp 1 người qua nhiều page
- unauthorized access query

## 14.4 Authorization tests
Các case bắt buộc:
- user đúng tenant, đúng role → allow
- user đúng tenant, sai role → deny
- user khác tenant → deny
- user có explicit allow → allow
- secret document không có role phù hợp → deny

---

## 15. Deployment plan

## 15.1 Runtime
- FastAPI bằng uvicorn/gunicorn
- Qdrant bằng Docker volume persistent
- Ollama local service hoặc internal node

## 15.2 Workers
- một worker ingestion riêng
- một API service riêng

## 15.3 Process separation
- API không nên làm full reindex đồng bộ ngay trong request lâu
- reindex nên chạy background worker hoặc background task

FastAPI có `BackgroundTasks` cho các tác vụ chạy sau khi trả response, hữu ích cho job không cần giữ client chờ. citeturn962842search22

---

## 16. Roadmap triển khai

## Phase 1 — Stable foundation
- Kết nối SQL
- Clean OCR
- Chunking chuẩn
- Embed Ollama
- Upsert Qdrant
- `/chat` basic

## Phase 2 — Enterprise retrieval
- Keyword fallback
- Fusion
- better logging
- request_id
- source tracing

## Phase 3 — Data authorization
- JWT auth
- `UserContext`
- Qdrant auth filter
- audit logs
- denial handling

## Phase 4 — Production polish
- `/chat/stream`
- rerank
- incremental sync
- reindex by doc
- dashboard metrics

---

## 17. Deliverables của full enterprise RAG kit

### Code deliverables
- `config.py`
- `ollama.py`
- `sql.py`
- `qdrant.py`
- `authorization.py`
- `ingest_ocr.py`
- `retrieval.py`
- `rag.py`
- `main.py`
- `chat_console.py`

### Ops deliverables
- `.env.example`
- docker compose cho Qdrant
- runbook ingest
- runbook incident handling

### Security deliverables
- JWT validation
- role-to-sensitivity matrix
- audit schema
- access test cases

---

## 18. Quy tắc triển khai bắt buộc
- Không retrieve chunk ngoài quyền rồi mới lọc bằng app code.
- Không trả lời nếu không có context hợp lệ.
- Không hallucinate khi OCR không rõ.
- Mọi answer phải trả kèm sources.
- Mọi request nhạy cảm phải có audit log.

---

## 19. Next implementation order
1. Viết `authorization.py` với `UserContext` + `build_auth_filter()`.
2. Viết `ingest_ocr.py` hỗ trợ metadata quyền.
3. Viết `retrieval.py` với dense + keyword fallback.
4. Viết `rag.py` dùng filter theo quyền.
5. Viết `main.py` với `/chat` và `/chat/stream`.
6. Viết test cases cho access control.

---

## 20. Gợi ý triển khai quyền thực tế
Nếu bạn chưa có sẵn bảng quyền tài liệu, có thể bắt đầu bằng bảng mapping như sau:

### `DocumentPermission`
- `DocumentId`
- `TenantId`
- `Department`
- `Sensitivity`
- `AllowedRole`
- `AllowedUserId`

Khi ingest:
- join `OCRDocuments` với `DocumentPermission`
- đẩy metadata quyền lên từng chunk

Như vậy retrieval chỉ cần đọc claims của user và build Qdrant filter.

---

## 21. Kết luận
Bản enterprise RAG kit này không chỉ là chat với vector DB, mà là một nền retrieval có kiểm soát truy cập, logging, fallback, và khả năng scale dần.

Trọng tâm thành công:
- clean OCR tốt
- chunk đúng
- metadata quyền đầy đủ
- filter quyền ngay tại Qdrant
- answer chỉ dựa trên context

