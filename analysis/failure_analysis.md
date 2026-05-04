# Failure Analysis — Lab 18: Production RAG

**Nhóm:** Solo (Trần Ngọc Huy)  
**Thành viên:** Trần Ngọc Huy · 2A202600298 → M1, M2, M3, M4, M5

---

## RAGAS Scores

| Metric | Naive Baseline | Production | Δ |
|--------|---------------|------------|---|
| Faithfulness | 1.0000 | 0.8750 | -0.1250 |
| Answer Relevancy | 0.3064 | 0.4370 | +0.1306 |
| Context Precision | 1.0000 | 0.9750 | -0.0250 |
| Context Recall | 1.0000 | 1.0000 | +0.0000 |

## Bottom-5 Failures

### #1
- **Question:** Phụ cấp ăn uống công tác tại Hà Nội là bao nhiêu mỗi ngày?
- **Expected:** Phụ cấp ăn uống 300.000 đồng mỗi ngày cho công tác tại Hà Nội và TP. Hồ Chí Minh.
- **Got:** (LLM Hallucination/No info)
- **Worst metric:** faithfulness (0.0)
- **Error Tree:** Output sai → Context đúng? → Có → Query OK? → Có
- **Root cause:** LLM không tìm thấy hoặc không hiểu con số 300.000 trong context mặc dù context chứa thông tin.
- **Suggested fix:** Cải thiện prompt template để LLM chú ý hơn đến các con số cụ thể hoặc dùng model mạnh hơn.

### #2
- **Question:** Thâm niên công tác ảnh hưởng thế nào đến số ngày nghỉ phép?
- **Expected:** Số ngày nghỉ phép tăng thêm 1 ngày cho mỗi 5 năm thâm niên công tác.
- **Worst metric:** answer_relevancy (0.321)
- **Error Tree:** Output đúng? → Có → Context đúng? → Có → Query OK? → Có
- **Root cause:** Câu trả lời của LLM quá ngắn gọn hoặc format không khớp với kỳ vọng của RAGAS evaluation.
- **Suggested fix:** Yêu cầu LLM trả lời chi tiết hơn và trích dẫn trực tiếp từ tài liệu.

### #3
- **Question:** Ngày nghỉ phép không dùng hết có thể chuyển sang năm sau tối đa bao nhiêu ngày?
- **Expected:** Ngày nghỉ phép không sử dụng có thể chuyển sang năm tiếp theo tối đa 5 ngày.
- **Worst metric:** answer_relevancy (0.410)
- **Error Tree:** Output đúng? → Có → Context đúng? → Có
- **Root cause:** Tương tự câu #2, điểm relevancy thấp do vocab gap giữa câu trả lời và ground truth.
- **Suggested fix:** Sử dụng HyQA (M5) để làm giàu vocabulary cho chunks giúp retrieval và generation đồng nhất hơn.

### #4
- **Question:** Im lặng có được coi là đồng ý xử lý dữ liệu cá nhân không?
- **Expected:** Im lặng hoặc không phản hồi không được coi là sự đồng ý.
- **Worst metric:** answer_relevancy (0.0)
- **Error Tree:** Output sai → Context đúng? → Có
- **Root cause:** LLM có thể trả lời vòng vo hoặc phủ định không rõ ràng so với ground truth.
- **Suggested fix:** Tighten system prompt để bắt LLM trả lời trực diện "Có" hoặc "Không" kèm giải thích.

### #5
- **Question:** Mật khẩu phải thay đổi sau bao nhiêu ngày?
- **Expected:** Mật khẩu phải thay đổi mỗi 90 ngày.
- **Worst metric:** faithfulness (0.5)
- **Error Tree:** Output đúng? → Có → Context đúng? → Có
- **Root cause:** Có thể context chứa nhiều thông tin về mật khẩu (độ dài, ký tự đặc biệt) làm LLM bị phân tâm khi trích xuất số ngày.
- **Suggested fix:** Reranking (M3) tốt hơn để chỉ lấy chunk chứa thông tin "90 ngày" lên đầu.

## Case Study (cho presentation)

**Question chọn phân tích:** "Phụ cấp ăn uống công tác tại Hà Nội là bao nhiêu mỗi ngày?"

**Error Tree walkthrough:**
1. Output đúng? → Không.
2. Context đúng? → Có (Context recall = 1.0, precision = 1.0).
3. Query rewrite OK? → Có.
4. Fix ở bước: **Generation (G)**.

**Nếu có thêm 1 giờ, sẽ optimize:**
- Thêm bước **Query Expansion/Rewrite** ở Pre-RAG để làm rõ các câu hỏi về con số.
- Tinh chỉnh Prompt để LLM tập trung vào việc trích xuất chính xác các thực thể (entities) và định lượng (quantities).
