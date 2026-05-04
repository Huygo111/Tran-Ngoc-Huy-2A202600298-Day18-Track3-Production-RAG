# Group Report — Lab 18: Production RAG

**Nhóm:** Solo (Trần Ngọc Huy)  
**Ngày:** 2026-05-04

## Thành viên & Phân công

| Tên | Module | Hoàn thành | Tests pass |
|-----|--------|-----------|-----------|
| Trần Ngọc Huy | M1: Chunking | [x] | 8/8 |
| Trần Ngọc Huy | M2: Hybrid Search | [x] | 5/5 |
| Trần Ngọc Huy | M3: Reranking | [x] | 5/5 |
| Trần Ngọc Huy | M4: Evaluation | [x] | 4/4 |
| Trần Ngọc Huy | M5: Enrichment | [x] | 10/10 |

## Kết quả RAGAS

| Metric | Naive | Production | Δ |
|--------|-------|-----------|---|
| Faithfulness | 1.0000 | 0.8750 | -0.1250 |
| Answer Relevancy | 0.3064 | 0.4370 | +0.1306 |
| Context Precision | 1.0000 | 0.9750 | -0.0250 |
| Context Recall | 1.0000 | 1.0000 | +0.0000 |

## Key Findings

1. **Biggest improvement:** `Answer Relevancy` tăng đáng kể nhờ việc kết hợp **Hybrid Search** và **Enrichment (HyQA)**. Việc tạo ra các câu hỏi giả định giúp thu hẹp khoảng cách từ vựng giữa câu hỏi người dùng và nội dung tài liệu.
2. **Biggest challenge:** Việc xử lý mã hóa tiếng Việt (Unicode) trên Windows console gây ra nhiều lỗi `UnicodeEncodeError`. Giải pháp là phải loại bỏ các ký tự đặc biệt trong các lệnh `print` và đảm bảo encoding UTF-8 khi đọc/ghi file.
3. **Surprise finding:** `Faithfulness` của bản Production thấp hơn bản Naive. Nguyên nhân là do bản Production lấy ra nhiều context hơn (nhờ Reranking chọn được top-k chất lượng cao), nhưng LLM đôi khi bị "nhiễu" bởi quá nhiều thông tin và đưa thêm các ý ngoài lề vào câu trả lời.

## Presentation Notes (5 phút)

1. RAGAS scores (naive vs production): Production cải thiện Relevancy nhưng cần kiểm soát Hallucination chặt hơn.
2. Biggest win — module nào, tại sao: **M3 Reranking** giúp đưa đúng thông tin cần thiết lên đầu, giúp LLM trả lời trúng trọng tâm hơn.
3. Case study — 1 failure, Error Tree walkthrough: Câu hỏi về "Phụ cấp ăn uống" bị sai ở bước Generation mặc dù Retrieval đã lấy đúng context.
4. Next optimization nếu có thêm 1 giờ: Tối ưu prompt generation và thử nghiệm các mô hình LLM lớn hơn (như GPT-4o) để kiểm tra tính ổn định của câu trả lời.
