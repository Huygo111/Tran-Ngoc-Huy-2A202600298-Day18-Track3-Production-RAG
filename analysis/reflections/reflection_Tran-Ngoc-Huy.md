# Individual Reflection — Lab 18

**Tên:** Trần Ngọc Huy  
**Module phụ trách:** M1, M2, M3, M4, M5 (Làm solo)

---

## 1. Đóng góp kỹ thuật

- Module đã implement: Tất cả 5 modules của bài lab.
- Các hàm/class chính đã viết: 
    - M1: `chunk_semantic`, `chunk_hierarchical`, `chunk_structure_aware`.
    - M2: `BM25Search`, `DenseSearch`, `reciprocal_rank_fusion`.
    - M3: `CrossEncoderReranker`, `benchmark_reranker`.
    - M4: `evaluate_ragas`, `failure_analysis`.
    - M5: `enrich_chunks`, `generate_hypothesis_questions`.
- Số tests pass: 37/37 (toàn bộ tests của 5 modules).

## 2. Kiến thức học được

- Khái niệm mới nhất: **Enrichment Pipeline** và **Contextual Retrieval**. Việc làm giàu chunk bằng LLM trước khi indexing giúp cải thiện retrieval đáng kể.
- Điều bất ngờ nhất: RAGAS evaluation có thể tự động diagnosis lỗi dựa trên 4 metrics cốt lõi, giúp việc debug pipeline trở nên có hệ thống hơn.
- Kết nối với bài giảng (slide nào): Kết nối với slide về "Production RAG Architecture" và "Advanced Retrieval Strategies" (Hybrid Search, Reranking).

## 3. Khó khăn & Cách giải quyết

- Khó khăn lớn nhất: Lỗi `UnicodeEncodeError` trên Windows console khi in các câu hỏi tiếng Việt hoặc ký tự đặc biệt.
- Cách giải quyết: Tùy chỉnh lại các lệnh print, loại bỏ emoji và ký tự không thuộc bảng mã CP1252 (hoặc chuyển sang log file thay vì console). Đồng thời monkey-patch lại một số hàm của `ragas` để tương thích với thư viện `openai` mới nhất.
- Thời gian debug: Khoảng 2 giờ cho các lỗi về môi trường và encoding.

## 4. Nếu làm lại

- Sẽ làm khác điều gì: Sử dụng Qdrant Docker thay vì in-memory để dữ liệu được bền vững hơn và có thể trực quan hóa trên Dashboard.
- Module nào muốn thử tiếp: M5 (Enrichment) sâu hơn, đặc biệt là phần trích xuất kiến thức (Knowledge Graph) từ chunks.

## 5. Tự đánh giá

| Tiêu chí | Tự chấm (1-5) |
|----------|---------------|
| Hiểu bài giảng | 5 |
| Code quality | 5 |
| Teamwork | 5 (Làm solo nhưng phối hợp tốt với hướng dẫn) |
| Problem solving | 5 |
