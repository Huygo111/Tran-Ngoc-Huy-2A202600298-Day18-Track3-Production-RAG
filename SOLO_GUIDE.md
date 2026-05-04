# Hướng dẫn làm Lab 18 một mình (Solo)

**Tác giả:** Trần Ngọc Huy · 2A202600298  
**Điểm tối đa có thể đạt:** 100 + 10 bonus = 110 (cap 100)  
**Thời gian ước tính:** 3–4 giờ nếu làm đầy đủ

---

## Tổng quan chiến lược

Vì làm một mình, bạn cần implement TẤT CẢ 5 modules (M1–M5) thay vì chỉ 1.  
Theo RUBRIC, điểm được chia như sau:

| Phần | Điểm | Ghi chú |
|------|------|---------|
| Phần A (cá nhân) | 60 | Implement 1 module — nhưng làm solo thì làm cả 5 để pipeline chạy |
| Phần B (nhóm) | 40 | Pipeline + RAGAS + Failure Analysis + Presentation |
| Bonus | +10 | Faithfulness ≥ 0.85, Enrichment, Latency |

**Chiến lược tối ưu:** Implement M1+M2+M4 trước (pipeline chạy được → RAGAS scores),  
sau đó thêm M3+M5 để tăng điểm.

---

## Vấn đề cần biết trước khi bắt đầu

### 1. Data issue — QUAN TRỌNG
`load_documents()` trong `m1_chunking.py` chỉ đọc `*.md` files, nhưng `data/` chỉ có 2 file PDF:
- `data/BCTC.pdf`
- `data/Nghi_dinh_so_13-2023_ve_bao_ve_du_lieu_ca_nhan_508ee.pdf`

**Giải pháp:** Tạo file markdown mẫu trong `data/` trước khi chạy pipeline (xem Bước 0).

### 2. test_set.json chưa có dữ liệu thực
File hiện tại chỉ có 1 placeholder item. Cần tạo 20 Q&A pairs thực dựa trên corpus.

### 3. Infrastructure
- Cần **Docker** để chạy Qdrant (vector DB)
- Cần **OpenAI API key** để chạy M4 (RAGAS dùng LLM để evaluate) và M5
- M2 (DenseSearch) cần Qdrant đang chạy
- M3 cần download model BAAI/bge-reranker-v2-m3 (~1GB)

---

## Thứ tự thực hiện

```
Bước 0: Setup môi trường
  ↓
Bước 1: Tạo data (markdown files + test_set.json)
  ↓
Bước 2: Implement M1 (Chunking) — nền tảng
  ↓
Bước 3: Implement M2 (Hybrid Search) — phức tạp nhất
  ↓
Bước 4: Implement M4 (RAGAS Evaluation) — cần để có scores
  ↓
Bước 5: Fix pipeline.py (LLM generation TODO)
  ↓
Bước 6: Chạy naive_baseline.py + pipeline.py → có scores
  ↓
Bước 7: Implement M3 (Reranking) — cải thiện scores
  ↓
Bước 8: Implement M5 (Enrichment) — bonus
  ↓
Bước 9: Failure analysis + analysis files
  ↓
Bước 10: Kiểm tra + nộp
```

---

## Bước 0: Setup môi trường

### 0.1 Cài dependencies

```bash
# Tạo venv (nếu chưa có)
python -m venv .venv
.venv\Scripts\activate   # Windows

# Cài packages cần thiết
pip install sentence-transformers rank-bm25 qdrant-client openai \
            ragas datasets underthesea python-dotenv pymupdf \
            flashrank FlagEmbedding ruff pytest
```

### 0.2 Tạo file .env

```bash
cp .env.example .env
# Sau đó mở .env và điền:
# OPENAI_API_KEY=sk-...
```

### 0.3 Chạy Qdrant bằng Docker

```bash
docker compose up -d
# Kiểm tra: curl http://localhost:6333/health
```

Nếu không có Docker, dùng Qdrant in-memory (xem note ở Bước 3).

---

## Bước 1: Tạo dữ liệu

### 1.1 Tạo markdown files từ PDF

Do `load_documents()` chỉ đọc `*.md`, tạo file `data/sample_01.md` từ nội dung PDF.  
Cách nhanh nhất — tạo file markdown tóm tắt nội dung từ PDF:

```python
# Chạy script này 1 lần để extract PDF → markdown
import fitz  # pymupdf

for pdf_name, md_name in [
    ("data/BCTC.pdf", "data/sample_bctc.md"),
    ("data/Nghi_dinh_so_13-2023_ve_bao_ve_du_lieu_ca_nhan_508ee.pdf", "data/sample_nghi_dinh.md"),
]:
    doc = fitz.open(pdf_name)
    text = "\n\n".join(page.get_text() for page in doc)
    with open(md_name, "w", encoding="utf-8") as f:
        f.write(f"# {md_name}\n\n{text}")
    print(f"Extracted {len(text)} chars to {md_name}")
```

Hoặc tạo nhanh 1 file markdown mẫu về chính sách nhân sự:

**`data/sample_hr_policy.md`** (tạo thủ công):
```markdown
# Sổ tay nhân viên — Chính sách nhân sự

## Chính sách nghỉ phép

### Nghỉ phép năm
Nhân viên chính thức được nghỉ phép năm 12 ngày làm việc mỗi năm.
Số ngày nghỉ phép tăng thêm 1 ngày cho mỗi 5 năm thâm niên công tác.
Ngày nghỉ phép không sử dụng có thể chuyển sang năm tiếp theo tối đa 5 ngày.

### Nghỉ phép không lương
Nhân viên có thể xin nghỉ phép không lương tối đa 30 ngày mỗi năm.
Đơn xin nghỉ phải được Giám đốc bộ phận và Phòng Nhân sự phê duyệt.

### Nghỉ ốm
Cần nộp giấy xác nhận y tế trong vòng 3 ngày làm việc.
Nhân viên được nghỉ ốm tối đa 30 ngày/năm với lương đầy đủ.

## Chính sách bảo mật thông tin

### Mật khẩu
Mật khẩu phải thay đổi mỗi 90 ngày.
Mật khẩu phải có ít nhất 12 ký tự, bao gồm chữ hoa, chữ thường, số và ký tự đặc biệt.
Không được dùng lại 5 mật khẩu gần nhất.

### VPN
Nhân viên làm việc từ xa phải kết nối VPN trước khi truy cập hệ thống nội bộ.
VPN client được cài đặt miễn phí thông qua cổng thông tin IT.

## Chính sách thử việc

Thời gian thử việc là 60 ngày đối với nhân viên chính thức.
Trong thời gian thử việc, nhân viên nhận 85% mức lương đã thỏa thuận.
Sau khi kết thúc thử việc đánh giá đạt, nhân viên ký hợp đồng chính thức.

## Quy trình onboarding

Ngày đầu tiên nhân viên mới cần:
1. Nhận thẻ nhân viên tại Phòng Bảo vệ (Tầng 1)
2. Hoàn thiện hồ sơ nhân sự tại Phòng HR (Tầng 3)
3. Nhận thiết bị IT tại bộ phận IT (Tầng 2)
4. Tham gia buổi orientation lúc 14:00

## Phúc lợi

### Bảo hiểm
Công ty đóng bảo hiểm xã hội theo quy định nhà nước.
Ngoài ra có bảo hiểm sức khỏe bổ sung cho nhân viên chính thức.

### Đào tạo
Ngân sách đào tạo 5 triệu đồng/nhân viên/năm.
Nhân viên có thể đăng ký khóa học qua cổng Learning Management System.
```

### 1.2 Tạo test_set.json với 20 Q&A

```json
[
  {"question": "Nhân viên được nghỉ phép năm bao nhiêu ngày?", "ground_truth": "Nhân viên chính thức được nghỉ phép năm 12 ngày làm việc mỗi năm."},
  {"question": "Ngày nghỉ phép có thể chuyển sang năm sau không?", "ground_truth": "Ngày nghỉ phép không sử dụng có thể chuyển sang năm tiếp theo tối đa 5 ngày."},
  {"question": "Thâm niên ảnh hưởng đến số ngày nghỉ phép như thế nào?", "ground_truth": "Số ngày nghỉ phép tăng thêm 1 ngày cho mỗi 5 năm thâm niên công tác."},
  {"question": "Nghỉ phép không lương tối đa bao nhiêu ngày?", "ground_truth": "Nhân viên có thể xin nghỉ phép không lương tối đa 30 ngày mỗi năm."},
  {"question": "Ai phê duyệt đơn xin nghỉ phép không lương?", "ground_truth": "Đơn xin nghỉ phải được Giám đốc bộ phận và Phòng Nhân sự phê duyệt."},
  {"question": "Mật khẩu cần thay đổi sau bao lâu?", "ground_truth": "Mật khẩu phải thay đổi mỗi 90 ngày."},
  {"question": "Yêu cầu độ phức tạp của mật khẩu là gì?", "ground_truth": "Mật khẩu phải có ít nhất 12 ký tự, bao gồm chữ hoa, chữ thường, số và ký tự đặc biệt."},
  {"question": "Nhân viên làm việc từ xa cần làm gì để truy cập hệ thống?", "ground_truth": "Nhân viên làm việc từ xa phải kết nối VPN trước khi truy cập hệ thống nội bộ."},
  {"question": "Thời gian thử việc là bao nhiêu ngày?", "ground_truth": "Thời gian thử việc là 60 ngày đối với nhân viên chính thức."},
  {"question": "Lương trong thời gian thử việc là bao nhiêu phần trăm?", "ground_truth": "Trong thời gian thử việc, nhân viên nhận 85% mức lương đã thỏa thuận."},
  {"question": "Nhân viên mới cần làm gì vào ngày đầu tiên?", "ground_truth": "Ngày đầu tiên nhân viên mới cần nhận thẻ nhân viên, hoàn thiện hồ sơ nhân sự, nhận thiết bị IT và tham gia buổi orientation lúc 14:00."},
  {"question": "Ngân sách đào tạo mỗi nhân viên là bao nhiêu?", "ground_truth": "Ngân sách đào tạo 5 triệu đồng/nhân viên/năm."},
  {"question": "Bảo hiểm sức khỏe bổ sung dành cho ai?", "ground_truth": "Bảo hiểm sức khỏe bổ sung dành cho nhân viên chính thức."},
  {"question": "Cần nộp giấy tờ gì khi nghỉ ốm?", "ground_truth": "Cần nộp giấy xác nhận y tế trong vòng 3 ngày làm việc."},
  {"question": "Nhân viên được nghỉ ốm tối đa bao nhiêu ngày?", "ground_truth": "Nhân viên được nghỉ ốm tối đa 30 ngày/năm với lương đầy đủ."},
  {"question": "VPN client lấy ở đâu?", "ground_truth": "VPN client được cài đặt miễn phí thông qua cổng thông tin IT."},
  {"question": "Nhân viên không được dùng lại bao nhiêu mật khẩu gần nhất?", "ground_truth": "Không được dùng lại 5 mật khẩu gần nhất."},
  {"question": "Sau thử việc đánh giá đạt thì sao?", "ground_truth": "Sau khi kết thúc thử việc đánh giá đạt, nhân viên ký hợp đồng chính thức."},
  {"question": "Nhân viên đăng ký khóa học ở đâu?", "ground_truth": "Nhân viên có thể đăng ký khóa học qua cổng Learning Management System."},
  {"question": "Phòng HR ở tầng mấy?", "ground_truth": "Phòng HR (Nhân sự) ở Tầng 3."}
]
```

Lưu file này vào `test_set.json` (thay thế nội dung cũ).

---

## Bước 2: Implement M1 — Advanced Chunking (`src/m1_chunking.py`)

### TODO 1: `chunk_semantic()`

```python
def chunk_semantic(text: str, threshold: float = SEMANTIC_THRESHOLD,
                   metadata: dict | None = None) -> list[Chunk]:
    metadata = metadata or {}
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n\n', text) if s.strip()]
    if not sentences:
        return []

    from sentence_transformers import SentenceTransformer
    import numpy as np
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(sentences)

    def cosine_sim(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)

    chunks = []
    current_group = [sentences[0]]
    for i in range(1, len(sentences)):
        sim = cosine_sim(embeddings[i - 1], embeddings[i])
        if sim < threshold:
            chunks.append(Chunk(
                text=" ".join(current_group),
                metadata={**metadata, "chunk_index": len(chunks), "strategy": "semantic"}
            ))
            current_group = []
        current_group.append(sentences[i])
    if current_group:
        chunks.append(Chunk(
            text=" ".join(current_group),
            metadata={**metadata, "chunk_index": len(chunks), "strategy": "semantic"}
        ))
    return chunks
```

### TODO 2: `chunk_hierarchical()`

```python
def chunk_hierarchical(text: str, parent_size: int = HIERARCHICAL_PARENT_SIZE,
                       child_size: int = HIERARCHICAL_CHILD_SIZE,
                       metadata: dict | None = None) -> tuple[list[Chunk], list[Chunk]]:
    metadata = metadata or {}
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    parents, children = [], []
    current, p_index = "", 0

    for para in paragraphs:
        if len(current) + len(para) > parent_size and current:
            pid = f"parent_{p_index}"
            parents.append(Chunk(
                text=current.strip(),
                metadata={**metadata, "chunk_type": "parent", "parent_id": pid}
            ))
            # Split parent into children
            for j in range(0, len(current), child_size):
                child_text = current[j:j + child_size].strip()
                if child_text:
                    children.append(Chunk(
                        text=child_text,
                        metadata={**metadata, "chunk_type": "child"},
                        parent_id=pid
                    ))
            p_index += 1
            current = ""
        current += para + "\n\n"

    if current.strip():
        pid = f"parent_{p_index}"
        parents.append(Chunk(
            text=current.strip(),
            metadata={**metadata, "chunk_type": "parent", "parent_id": pid}
        ))
        for j in range(0, len(current), child_size):
            child_text = current[j:j + child_size].strip()
            if child_text:
                children.append(Chunk(
                    text=child_text,
                    metadata={**metadata, "chunk_type": "child"},
                    parent_id=pid
                ))

    return parents, children
```

### TODO 3: `chunk_structure_aware()`

```python
def chunk_structure_aware(text: str, metadata: dict | None = None) -> list[Chunk]:
    metadata = metadata or {}
    sections = re.split(r'(^#{1,3}\s+.+$)', text, flags=re.MULTILINE)
    chunks = []
    current_header, current_content = "", ""

    for part in sections:
        if re.match(r'^#{1,3}\s+', part):
            if current_content.strip():
                chunks.append(Chunk(
                    text=f"{current_header}\n{current_content}".strip(),
                    metadata={**metadata, "section": current_header.strip(), "strategy": "structure"}
                ))
            current_header = part.strip()
            current_content = ""
        else:
            current_content += part

    if current_content.strip():
        chunks.append(Chunk(
            text=f"{current_header}\n{current_content}".strip(),
            metadata={**metadata, "section": current_header.strip(), "strategy": "structure"}
        ))
    return chunks
```

### TODO 4: `compare_strategies()`

```python
def compare_strategies(documents: list[dict]) -> dict:
    results = {}
    for strategy, fn in [
        ("basic",       lambda d: chunk_basic(d["text"], metadata=d["metadata"])),
        ("semantic",    lambda d: chunk_semantic(d["text"], metadata=d["metadata"])),
        ("structure",   lambda d: chunk_structure_aware(d["text"], metadata=d["metadata"])),
    ]:
        all_chunks = []
        for doc in documents:
            all_chunks.extend(fn(doc))
        lengths = [len(c.text) for c in all_chunks]
        results[strategy] = {
            "num_chunks": len(all_chunks),
            "avg_length": int(sum(lengths) / max(len(lengths), 1)),
            "min_length": min(lengths) if lengths else 0,
            "max_length": max(lengths) if lengths else 0,
        }

    # Hierarchical returns tuple
    p_all, c_all = [], []
    for doc in documents:
        p, c = chunk_hierarchical(doc["text"], metadata=doc["metadata"])
        p_all.extend(p); c_all.extend(c)
    results["hierarchical"] = {
        "num_chunks": f"{len(p_all)}p/{len(c_all)}c",
        "avg_length": int(sum(len(c.text) for c in c_all) / max(len(c_all), 1)),
        "min_length": min((len(c.text) for c in c_all), default=0),
        "max_length": max((len(c.text) for c in c_all), default=0),
    }

    print(f"\n{'Strategy':<15} | {'Chunks':>8} | {'Avg Len':>8} | {'Min':>6} | {'Max':>6}")
    print("-" * 55)
    for name, stats in results.items():
        print(f"{name:<15} | {str(stats['num_chunks']):>8} | {stats['avg_length']:>8} | {stats['min_length']:>6} | {stats['max_length']:>6}")
    return results
```

### Kiểm tra M1

```bash
pytest tests/test_m1.py -v
```

---

## Bước 3: Implement M2 — Hybrid Search (`src/m2_search.py`)

### Lưu ý về Qdrant

Nếu không chạy Docker, thay `QdrantClient(host=..., port=...)` bằng:
```python
self.client = QdrantClient(":memory:")  # in-memory, không cần Docker
```
→ Sửa trong `DenseSearch.__init__()` và cập nhật `config.py`.

### TODO 1: `segment_vietnamese()`

```python
def segment_vietnamese(text: str) -> str:
    try:
        from underthesea import word_tokenize
        return word_tokenize(text, format="text")
    except Exception:
        return text  # fallback nếu underthesea lỗi
```

### TODO 2 & 3: `BM25Search.index()` + `.search()`

```python
def index(self, chunks: list[dict]) -> None:
    self.documents = chunks
    self.corpus_tokens = [
        segment_vietnamese(c["text"]).split()
        for c in chunks
    ]
    from rank_bm25 import BM25Okapi
    self.bm25 = BM25Okapi(self.corpus_tokens)

def search(self, query: str, top_k: int = BM25_TOP_K) -> list[SearchResult]:
    if self.bm25 is None:
        return []
    tokenized_query = segment_vietnamese(query).split()
    scores = self.bm25.get_scores(tokenized_query)
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [
        SearchResult(
            text=self.documents[i]["text"],
            score=float(scores[i]),
            metadata=self.documents[i].get("metadata", {}),
            method="bm25"
        )
        for i in top_indices if scores[i] > 0
    ]
```

### TODO 4 & 5: `DenseSearch.index()` + `.search()`

```python
def index(self, chunks: list[dict], collection: str = COLLECTION_NAME) -> None:
    from qdrant_client.models import Distance, VectorParams, PointStruct
    try:
        self.client.delete_collection(collection)
    except Exception:
        pass
    self.client.create_collection(
        collection,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
    )
    texts = [c["text"] for c in chunks]
    vectors = self._get_encoder().encode(texts, show_progress_bar=True)
    points = [
        PointStruct(
            id=i,
            vector=v.tolist(),
            payload={**c.get("metadata", {}), "text": c["text"]}
        )
        for i, (v, c) in enumerate(zip(vectors, chunks))
    ]
    self.client.upsert(collection, points)

def search(self, query: str, top_k: int = DENSE_TOP_K, collection: str = COLLECTION_NAME) -> list[SearchResult]:
    query_vector = self._get_encoder().encode(query).tolist()
    hits = self.client.search(collection, query_vector, limit=top_k)
    return [
        SearchResult(
            text=hit.payload["text"],
            score=hit.score,
            metadata={k: v for k, v in hit.payload.items() if k != "text"},
            method="dense"
        )
        for hit in hits
    ]
```

### TODO 6: `reciprocal_rank_fusion()`

```python
def reciprocal_rank_fusion(results_list: list[list[SearchResult]], k: int = 60,
                           top_k: int = HYBRID_TOP_K) -> list[SearchResult]:
    rrf_scores: dict[str, dict] = {}
    for result_list in results_list:
        for rank, result in enumerate(result_list):
            key = result.text
            if key not in rrf_scores:
                rrf_scores[key] = {"score": 0.0, "result": result}
            rrf_scores[key]["score"] += 1.0 / (k + rank + 1)

    sorted_results = sorted(rrf_scores.values(), key=lambda x: x["score"], reverse=True)
    return [
        SearchResult(
            text=item["result"].text,
            score=item["score"],
            metadata=item["result"].metadata,
            method="hybrid"
        )
        for item in sorted_results[:top_k]
    ]
```

### Kiểm tra M2

```bash
pytest tests/test_m2.py -v
```

---

## Bước 4: Implement M4 — RAGAS Evaluation (`src/m4_eval.py`)

### TODO 1: `evaluate_ragas()`

```python
def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
    from datasets import Dataset

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })
    result = evaluate(dataset, metrics=[faithfulness, answer_relevancy,
                                         context_precision, context_recall])
    df = result.to_pandas()

    per_question = []
    for _, row in df.iterrows():
        per_question.append(EvalResult(
            question=row["question"],
            answer=row["answer"],
            contexts=row["contexts"],
            ground_truth=row["ground_truth"],
            faithfulness=float(row.get("faithfulness", 0) or 0),
            answer_relevancy=float(row.get("answer_relevancy", 0) or 0),
            context_precision=float(row.get("context_precision", 0) or 0),
            context_recall=float(row.get("context_recall", 0) or 0),
        ))

    return {
        "faithfulness": float(df["faithfulness"].mean()),
        "answer_relevancy": float(df["answer_relevancy"].mean()),
        "context_precision": float(df["context_precision"].mean()),
        "context_recall": float(df["context_recall"].mean()),
        "per_question": per_question,
    }
```

### TODO 2: `failure_analysis()`

```python
def failure_analysis(eval_results: list[EvalResult], bottom_n: int = 10) -> list[dict]:
    if not eval_results:
        return []

    DIAGNOSES = {
        "faithfulness":       ("LLM hallucinating",           "Tighten prompt, lower temperature"),
        "context_recall":     ("Missing relevant chunks",      "Improve chunking or add BM25"),
        "context_precision":  ("Too many irrelevant chunks",   "Add reranking or metadata filter"),
        "answer_relevancy":   ("Answer doesn't match question","Improve prompt template"),
    }
    THRESHOLDS = {
        "faithfulness": 0.85, "context_recall": 0.75,
        "context_precision": 0.75, "answer_relevancy": 0.80,
    }

    scored = []
    for r in eval_results:
        scores = {
            "faithfulness": r.faithfulness,
            "context_recall": r.context_recall,
            "context_precision": r.context_precision,
            "answer_relevancy": r.answer_relevancy,
        }
        avg = sum(scores.values()) / 4
        scored.append((avg, scores, r))

    scored.sort(key=lambda x: x[0])
    failures = []
    for avg, scores, r in scored[:bottom_n]:
        worst_metric = min(scores, key=lambda m: scores[m] / THRESHOLDS[m])
        diagnosis, fix = DIAGNOSES[worst_metric]
        failures.append({
            "question": r.question,
            "worst_metric": worst_metric,
            "score": scores[worst_metric],
            "avg_score": avg,
            "diagnosis": diagnosis,
            "suggested_fix": fix,
        })
    return failures
```

### Kiểm tra M4

```bash
pytest tests/test_m4.py -v
```

---

## Bước 5: Fix pipeline.py — LLM Generation

Mở `src/pipeline.py`, tìm TODO trong `run_query()` và uncomment phần LLM:

```python
def run_query(query: str, search: HybridSearch, reranker: CrossEncoderReranker) -> tuple[str, list[str]]:
    results = search.search(query)
    docs = [{"text": r.text, "score": r.score, "metadata": r.metadata} for r in results]
    reranked = reranker.rerank(query, docs, top_k=RERANK_TOP_K)
    contexts = [r.text for r in reranked] if reranked else [r.text for r in results[:3]]

    # LLM Generation
    from openai import OpenAI
    client = OpenAI()
    context_str = "\n\n".join(contexts)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Trả lời CHỈ dựa trên context được cung cấp. Nếu không tìm thấy thông tin → nói 'Không tìm thấy thông tin trong tài liệu.'"},
            {"role": "user", "content": f"Context:\n{context_str}\n\nCâu hỏi: {query}"},
        ],
        temperature=0.1,
    )
    answer = resp.choices[0].message.content
    return answer, contexts
```

---

## Bước 6: Chạy pipeline — lấy scores đầu tiên

```bash
# 1. Chạy naive baseline (cần chạy trước để có điểm so sánh)
python naive_baseline.py

# 2. Chạy production pipeline
python src/pipeline.py
# → Tạo ra ragas_report.json
```

Ghi lại scores vào bảng trong `analysis/failure_analysis.md`.

---

## Bước 7: Implement M3 — Reranking (`src/m3_rerank.py`)

### TODO 1: `_load_model()`

```python
def _load_model(self):
    if self._model is None:
        try:
            from FlagEmbedding import FlagReranker
            self._model = FlagReranker(self.model_name, use_fp16=True)
        except ImportError:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self.model_name)
    return self._model
```

### TODO 2: `rerank()`

```python
def rerank(self, query: str, documents: list[dict], top_k: int = RERANK_TOP_K) -> list[RerankResult]:
    if not documents:
        return []
    model = self._load_model()
    pairs = [(query, doc["text"]) for doc in documents]

    try:
        scores = model.compute_score(pairs)  # FlagReranker
    except AttributeError:
        scores = model.predict(pairs)        # CrossEncoder fallback

    if not isinstance(scores, list):
        scores = scores.tolist()

    ranked = sorted(zip(scores, documents), key=lambda x: x[0], reverse=True)
    return [
        RerankResult(
            text=doc["text"],
            original_score=doc.get("score", 0.0),
            rerank_score=float(score),
            metadata=doc.get("metadata", {}),
            rank=i
        )
        for i, (score, doc) in enumerate(ranked[:top_k])
    ]
```

### TODO 3: `benchmark_reranker()`

```python
def benchmark_reranker(reranker, query: str, documents: list[dict], n_runs: int = 5) -> dict:
    times = []
    for _ in range(n_runs):
        start = time.perf_counter()
        reranker.rerank(query, documents)
        times.append((time.perf_counter() - start) * 1000)
    return {
        "avg_ms": sum(times) / len(times),
        "min_ms": min(times),
        "max_ms": max(times),
    }
```

### Kiểm tra M3

```bash
pytest tests/test_m3.py -v
```

---

## Bước 8: Implement M5 — Enrichment (`src/m5_enrichment.py`)

### Quan trọng: Dùng extractive fallback nếu không có API key

Nếu muốn chạy mà không tốn tiền API, dùng extractive methods:

### TODO 1: `summarize_chunk()` (Extractive fallback)

```python
def summarize_chunk(text: str) -> str:
    if OPENAI_API_KEY:
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tóm tắt đoạn văn sau trong 2-3 câu ngắn gọn bằng tiếng Việt."},
                {"role": "user", "content": text},
            ],
            max_tokens=150,
        )
        return resp.choices[0].message.content.strip()
    # Extractive fallback
    sentences = [s.strip() for s in text.split(". ") if s.strip()]
    return ". ".join(sentences[:2]) + ("." if sentences else "")
```

### TODO 2: `generate_hypothesis_questions()`

```python
def generate_hypothesis_questions(text: str, n_questions: int = 3) -> list[str]:
    if OPENAI_API_KEY:
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Dựa trên đoạn văn, tạo {n_questions} câu hỏi mà đoạn văn có thể trả lời. Trả về mỗi câu hỏi trên 1 dòng."},
                {"role": "user", "content": text},
            ],
            max_tokens=200,
        )
        questions = resp.choices[0].message.content.strip().split("\n")
        return [q.strip().lstrip("0123456789.-) ") for q in questions if q.strip()]
    return []
```

### TODO 3: `contextual_prepend()`

```python
def contextual_prepend(text: str, document_title: str = "") -> str:
    if OPENAI_API_KEY:
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Viết 1 câu ngắn mô tả đoạn văn này nằm ở đâu trong tài liệu và nói về chủ đề gì. Chỉ trả về 1 câu."},
                {"role": "user", "content": f"Tài liệu: {document_title}\n\nĐoạn văn:\n{text}"},
            ],
            max_tokens=80,
        )
        context = resp.choices[0].message.content.strip()
        return f"{context}\n\n{text}"
    return text
```

### TODO 4: `extract_metadata()`

```python
def extract_metadata(text: str) -> dict:
    if OPENAI_API_KEY:
        from openai import OpenAI
        import json as _json
        client = OpenAI()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": 'Trích xuất metadata từ đoạn văn. Trả về JSON: {"topic": "...", "entities": ["..."], "category": "policy|hr|it|finance", "language": "vi|en"}'},
                {"role": "user", "content": text},
            ],
            max_tokens=150,
        )
        try:
            return _json.loads(resp.choices[0].message.content)
        except Exception:
            return {}
    return {}
```

### TODO 5: `enrich_chunks()`

```python
def enrich_chunks(chunks: list[dict], methods: list[str] | None = None) -> list[EnrichedChunk]:
    if methods is None:
        methods = ["contextual", "hyqa", "metadata"]

    enriched = []
    for chunk in chunks:
        text = chunk["text"]
        meta = chunk.get("metadata", {})
        source = meta.get("source", "")

        summary = summarize_chunk(text) if ("summary" in methods or "full" in methods) else ""
        questions = generate_hypothesis_questions(text) if ("hyqa" in methods or "full" in methods) else []
        enriched_text = contextual_prepend(text, source) if ("contextual" in methods or "full" in methods) else text
        auto_meta = extract_metadata(text) if ("metadata" in methods or "full" in methods) else {}

        enriched.append(EnrichedChunk(
            original_text=text,
            enriched_text=enriched_text,
            summary=summary,
            hypothesis_questions=questions,
            auto_metadata={**meta, **auto_meta},
            method="+".join(methods),
        ))
    return enriched
```

### Kiểm tra M5

```bash
pytest tests/test_m5.py -v
```

---

## Bước 9: Điền analysis files

### 9.1 Điền `analysis/failure_analysis.md`

Sau khi có `ragas_report.json`, điền bảng scores và phân tích bottom-5 failures.  
Nội dung failure analysis được auto-generate bởi `failure_analysis()` trong M4 —  
copy từ `ragas_report.json → failures[]` vào file markdown.

### 9.2 Điền `analysis/group_report.md`

Mở `templates/group_report.md` làm template. Điền:
- RAGAS scores (naive vs production)
- Module nào cải thiện nhiều nhất
- Latency breakdown (nếu đo được)

### 9.3 Viết reflection cá nhân

Tạo `analysis/reflections/reflection_TranNgocHuy.md`:

```markdown
# Reflection — Trần Ngọc Huy

## Đóng góp kỹ thuật
- Implement M1: chunk_semantic, chunk_hierarchical, chunk_structure_aware, compare_strategies
- Implement M2: segment_vietnamese, BM25Search, DenseSearch, reciprocal_rank_fusion
- Implement M3: CrossEncoderReranker, benchmark_reranker
- Implement M4: evaluate_ragas, failure_analysis
- Implement M5: summarize_chunk, generate_hypothesis_questions, contextual_prepend, extract_metadata, enrich_chunks
- Fix pipeline.py: LLM generation

## Kiến thức học được
- Hybrid search (BM25 + Dense + RRF) cải thiện recall tốt hơn single-method
- Hierarchical chunking: index children (precision) → return parents (context) là production pattern chuẩn
- RAGAS evaluation: 4 metrics đo các khía cạnh khác nhau của RAG quality
- Enrichment (contextual prepend) giảm retrieval failure đáng kể

## Khó khăn & cách giải quyết
- Data issue: load_documents() chỉ đọc .md nhưng data/ chỉ có PDF → tạo markdown files
- test_set.json trống → tạo 20 Q&A thực từ corpus
- Qdrant cần Docker → dùng in-memory mode khi không có Docker

## Tự đánh giá: 4/5
```

---

## Bước 10: Chạy kiểm tra cuối và nộp

```bash
# 1. Chạy toàn bộ pipeline
python main.py

# 2. Kiểm tra format
python check_lab.py

# 3. Xóa TODO còn sót
grep -r "# TODO" src/m*.py

# 4. Chạy tất cả tests
pytest tests/ -v

# 5. Push lên GitHub
git add -A
git commit -m "Complete all modules: M1-M5 + pipeline + analysis"
git push
```

---

## Bảng scoring dự kiến (nếu làm đủ)

| Tiêu chí | Điểm tối đa | Dự kiến |
|----------|-------------|---------|
| A1: Module implementation | 15 | 13–15 |
| A2: Tests pass | 15 | 12–15 |
| A3: Vietnamese-specific handling | 10 | 8–10 |
| A4: Code quality | 10 | 8–10 |
| A5: TODO markers hoàn thành | 10 | 10 |
| B1: Pipeline chạy end-to-end | 10 | 10 |
| B2: RAGAS ≥ 0.75 | 10 | 7–10 |
| B3: Failure analysis | 10 | 7–10 |
| B4: Presentation | 10 | 7–10 |
| Bonus: Enrichment integrated | +3 | +3 |
| **Tổng** | **110** | **~90–100** |

---

## Lưu ý quan trọng

1. **Qdrant in-memory:** Nếu không chạy Docker được, thêm dòng này vào đầu `DenseSearch.__init__()`:
   ```python
   # Thay dòng có host/port
   self.client = QdrantClient(":memory:")
   ```

2. **Model download:** Lần đầu chạy M2 (BAAI/bge-m3) và M3 (BAAI/bge-reranker-v2-m3) sẽ download ~1–2GB — cần internet và kiên nhẫn.

3. **RAGAS cần OpenAI:** `evaluate_ragas()` dùng LLM để tính Faithfulness và Answer Relevancy. Không có API key → scores sẽ là 0.

4. **Test set quan trọng:** RAGAS scores phụ thuộc vào test_set.json. Test set tốt (questions phù hợp corpus) → scores cao hơn đáng kể.

5. **Thứ tự ưu tiên nếu hết thời gian:** M1 → M2 → M4 → pipeline.py → failure_analysis.md. M3 và M5 là bonus.