# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Công Việt Quang
**Nhóm:** A2
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (tiến gần đến 1) nghĩa là hai vector embedding có hướng gần giống nhau trong không gian vector đa chiều, thể hiện hai đoạn văn bản đó có nội dung ngữ nghĩa rất tương đồng hoặc gần gũi với nhau, bất kể độ dài hay độ lớn (magnitude) của vector khác nhau như thế nào.

**Ví dụ có độ tương tự CAO:**
- Câu A: Khách hàng có thể đổi trả sản phẩm trong vòng 7 ngày kể từ khi nhận hàng.
- Câu B: Người mua được quyền trả lại hàng và nhận hoàn tiền trong thời gian một tuần.
- Tại sao tương đồng: Cả hai câu diễn đạt cùng một chính sách quy định thời hạn đổi trả hàng (7 ngày / 1 tuần), mang cùng ngữ nghĩa dù dùng từ ngữ khác nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Điều khoản và điều kiện đổi trả hàng điện tử cho người mua.
- Câu B: Đội tuyển bóng đá nam đã giành huy chương vàng tại SEA Games.
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn độc lập (chính sách thương mại điện tử vs thể thao), các vector có hướng lệch nhau xa trong không gian embedding.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ quan tâm đến hướng của vector chứ không quan tâm đến độ lớn (magnitude), trong khi độ lớn của embedding có thể bị ảnh hưởng bởi độ dài văn bản chứ không phản ánh đúng ý nghĩa ngữ nghĩa. Do đó, hai câu có ý nghĩa giống nhau nhưng độ dài khác nhau vẫn cho ra cosine similarity cao, trong khi Euclidean distance có thể bị sai lệch bởi sự khác biệt về độ lớn vector.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
Bước nhảy (stride) giữa các chunk = chunk_size − overlap = 500 − 50 = 450
Công thức: số chunk = ⌈(tổng độ dài − overlap) / (chunk_size − overlap)⌉
= ⌈(10000 − 50) / 450⌉ = ⌈9950 / 450⌉ = ⌈22.11⌉ = 23

> *Đáp án:* **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, bước nhảy giảm còn 500 − 100 = 400, làm số chunk tăng lên khoảng 25 chunks (⌈9900/400⌉+1 = 25), tức là overlap càng lớn thì số chunk càng nhiều vì mỗi chunk "tiến" ít hơn qua tài liệu. Người ta muốn overlap lớn hơn để giữ được ngữ cảnh liên tục giữa các chunk, tránh mất thông tin quan trọng bị cắt ngang ở ranh giới giữa hai chunk, từ đó cải thiện độ chính xác khi truy xuất (retrieval).

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng biểu thức chính quy `re.split(r'(?<=[.!?])\s+|\n+', text)` để tách văn bản dựa trên các ranh giới kết thúc câu (`.`, `!`, `?` hoặc xuống dòng `\n`). Xử lý ngoại lệ văn bản rỗng (trả về `[]`) và dùng vòng lặp nhóm tối đa `max_sentences_per_chunk` câu lại thành một chunk liền mạch.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Áp dụng thuật toán chia đệ quy ưu tiên từ ranh giới lớn đến nhỏ theo danh sách `separators = ["\n\n", "\n", ". ", " ", ""]`. Base case là khi đoạn văn bản có độ dài <= chunksize hoặc danh sách separator rỗng (khi đó cắt cố định theo kích thước chunk_size). Nếu một phần tách vẫn quá dài, hàm tiếp tục gọi đệ quy `_split` với các separator ưu tiên thấp hơn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` duyệt từng Document, nhúng vector bằng `self._embedding_fn`, gán `metadata['doc_id']` mặc định và lưu dưới dạng dict vào `self._store`. `search` nhúng vector câu hỏi, tính điểm tương đồng bằng tích vô hướng `_dot` với tất cả chunk trong store, sắp xếp giảm dần theo điểm `score` và trả về `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Thực hiện quy tắc **Filter trước, Rank sau**: `search_with_filter` lọc danh sách `self._store` giữ lại các chunk khớp toàn bộ cặp key-value trong `metadata_filter` trước, sau đó mới tính tương đồng xếp hạng trên tập đã lọc. `delete_document` lọc loại bỏ mọi chunk có `metadata['doc_id'] == doc_id` và trả về `True` nếu số lượng chunk giảm đi.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `answer` gọi `self.store.search` để lấy `top_k` chunk liên quan nhất, ghép nội dung thành chuỗi ngữ cảnh context đánh số `[1]`, `[2]`. Sau đó chèn context và câu hỏi vào Prompt RAG theo mẫu quy định (chỉ trả lời dựa trên context) rồi truyền vào `self.llm_fn` để sinh ra câu trả lời cuối cùng.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================= test session starts =============================
platform win32 -- Python 3.13.2, pytest-9.1.1, pluggy-1.6.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.12s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Khách hàng có thể yêu cầu đổi trả trong 7 ngày. | Người mua được trả sản phẩm hoàn tiền trong 1 tuần. | cao | 0.9852 | Có |
| 2 | Thời gian giao hàng tiêu chuẩn từ 2 đến 4 ngày. | Khách nhận hàng sau 2-4 ngày kể từ khi đặt đơn. | cao | 0.9714 | Có |
| 3 | Chính sách bảo hành sản phẩm điện tử 12 tháng. | Đội tuyển Việt Nam giành chiến thắng 2-0 ở chung kết. | thấp | 0.0821 | Có |
| 4 | Người bán chịu phí dịch vụ 5% trên mỗi đơn hàng. | Sàn thu phí hoa hồng người bán là 5% tổng đơn. | cao | 0.9645 | Có |
| 5 | Mọi thông tin cá nhân của người dùng được mã hóa. | Thời tiết hôm nay trời nắng đẹp và nhiều mây. | thấp | 0.0412 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là các câu khác từ nhưng cùng ý nghĩa ngữ nghĩa (như 7 ngày vs 1 tuần) đạt điểm tương đồng gần như tuyệt đối (~0.98). Điều này cho thấy vector embeddings không chỉ trùng khớp từ vựng đơn thuần mà thể hiện sâu sắc vị trí ngữ nghĩa trong không gian đa chiều.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua có bao lâu để gửi yêu cầu trả hàng hoặc hoàn tiền sau khi giao thành công? | ...Khách hàng được trả hàng hoàn tiền trong vòng 15 ngày kể từ ngày giao thành công... (`shopee-terms-of-service`) | 0.3422 | Có | Trả lời đúng thời hạn 15 ngày đối với đơn hàng tiêu chuẩn và 24h đối với thực phẩm tươi sống. |
| 2 | Người mua bổ sung bằng chứng cho yêu cầu trả hàng hoặc hoàn tiền như thế nào? | ...Xác nhận bạn Đã nhận hoặc Chưa nhận hàng. Chọn lý do gửi yêu cầu. Tải lên bằng chứng... (`shopee-submit-return-request`) | 0.3762 | Có | Hướng dẫn tải video/hình ảnh qua mục Tôi > Trả hàng/Hoàn tiền. |
| 3 | Người bán phải đáp ứng yêu cầu gì về hình ảnh thật khi đăng sản phẩm trên Shopee? | ...a. Hình ảnh sản phẩm phải là ảnh chụp rõ, chi tiết tình trạng sản phẩm... (`shopee-product-listing-rules`) | 0.3232 | Có | Bài đăng phải có ít nhất 1 ảnh thật do người bán tự chụp, chiếm tối thiểu 40% diện tích. |
| 4 | Người bán không được đăng bán những nội dung hoặc sản phẩm nào trên Shopee? | ...Không được để những hình ảnh hoặc thông tin không phù hợp, bị cấm... (`shopee-product-listing-rules`) | 0.3614 | Có | Cấm bán hàng hóa vi phạm pháp luật, hàng giả, nội dung bạo lực/đồi trụy/xúc phạm. |
| 5 | Chi phí vận chuyển khi hoàn trả sản phẩm do bên nào chịu? | ...Chính sách bảo mật và phí vận chuyển hoàn trả hàng... (`shopee-terms-of-service`) | 0.3930 | Có | Người bán chịu phí nếu lỗi do người bán; người mua được hỗ trợ theo quy định sàn. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Sử dụng Metadata Filter (`customer_role`) giúp thu hẹp phạm vi tìm kiếm hiệu quả, loại bỏ nhiễu giữa các quy định của người bán và người mua. Chiến lược chia chunk theo ranh giới đoạn văn (RecursiveChunker) giúp duy trì tính mạch lạc ngữ cảnh tốt hơn chia theo kích thước cố định.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
