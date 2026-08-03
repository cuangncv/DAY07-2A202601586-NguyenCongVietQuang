# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Nhóm A2 <br>
**Thành viên:** 
1. Nguyễn Công Việt Quang - 2A202601586
2. Nguyễn Thị Thanh Hiền - 2A202601150
3. Đỗ Thành Đạt - 2A202601278
4. Trần Thị Hường - 2A202601648
5. Nguyễn Thành Công - 2A202601396 

**Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Nhóm tập trung vào chính sách trả hàng/hoàn tiền dành cho người mua và các quy định đăng bán, sản phẩm cấm/hạn chế dành cho người bán trên Shopee.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Quy định về đăng bán sản phẩm trên Shopee | https://help.shopee.vn/portal/4/article/77246 | 2026-08-03 / 2024-08-21 | 21.775 | `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `customer_role=seller` |
| 2 | Chính sách cấm hạn chế sản phẩm | https://help.shopee.vn/portal/4/article/77247 | 2026-08-03 / 2025-05-05 | 12.967 | Như trên; `customer_role=seller` |
| 3 | Chính sách trả hàng và hoàn tiền | https://help.shopee.vn/portal/4/article/77251?seo=1 | 2026-08-03 / 2026-03-11 | 19.656 | Như trên; `customer_role=both` |
| 4 | Quy trình Shopee xử lý yêu cầu trả hàng hoàn tiền | https://help.shopee.vn/portal/4/article/190242 | 2026-08-03 / không nêu | 8.180 | Như trên; `customer_role=buyer` |
| 5 | Các phương thức gửi hàng hoàn trả và phí hoàn trả | https://help.shopee.vn/portal/4/article/189477 | 2026-08-03 / không nêu | 5.910 | Như trên; `customer_role=buyer` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `shopee-return-refund-policy` | Xác định tài liệu chuẩn và chấm hit theo từng câu hỏi. |
| `customer_role` | enum | `buyer`, `seller`, `both` | Lọc đúng ngữ cảnh người mua/người bán, giảm kết quả nhiễu. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| shopee-product-listing-rules | FixedSizeChunker (`fixed_size`) | 107 | 199,62 | Trung bình; có thể cắt giữa điều/khoản |
| shopee-product-listing-rules | SentenceChunker (`by_sentences`) | 77 | 274,69 | Khá tốt với văn xuôi, nhưng danh sách dài dễ dồn chung |
| shopee-product-listing-rules | RecursiveChunker (`recursive`) | 154 | 136,73 | Tốt hơn ở ranh giới đoạn/dòng, nhiều chunk ngắn |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Nguyễn Công Việt Quang**
- **Loại chiến lược:** FixedSize (Fixed-small)
- **Mô tả & lý do chọn cho chủ đề này:** Dùng `chunk_size=400`, `overlap=50`. Kích thước nhỏ giúp truy xuất chính xác các quy định ngắn; overlap hạn chế mất ngữ cảnh tại ranh giới chunk.

**Thành viên 2 — Nguyễn Thị Thanh Hiền**
- **Loại chiến lược:** FixedSize (Fixed-large)
- **Mô tả & lý do chọn:** Dùng `chunk_size=800`, `overlap=120`. Chunk lớn giữ nhiều bối cảnh và giảm số chunk, nhưng có thể đưa thêm nội dung không liên quan vào kết quả.
- **Code snippet (nếu custom):** Không sử dụng chiến lược custom.

**Thành viên 3 — Đỗ Thành Đạt**
- **Loại chiến lược:** Sentence (Sentence-4)
- **Mô tả & lý do chọn:** Chia tối đa 4 câu/chunk nhằm giữ ranh giới ngôn ngữ tự nhiên. Cấu hình cho kết quả top-1 ổn định trên cả 5 câu hỏi với số chunk thấp hơn Fixed-small.
- **Code snippet (nếu custom):** Không sử dụng chiến lược custom.

**Thành viên 4 — Trần Thị Hường**
- **Loại chiến lược:** Recursive (Recursive-700)
- **Mô tả & lý do chọn:** Dùng `chunk_size=700`. Chiến lược chia đệ quy ưu tiên ranh giới đoạn và dòng trước khi cắt nhỏ, phù hợp với tài liệu chính sách có cấu trúc.
- **Code snippet (nếu custom):** Không sử dụng chiến lược custom.

**Thành viên 5 — Nguyễn Thành Công**
- **Loại chiến lược:** Custom (Policy-section)
- **Mô tả & lý do chọn:** Dùng `max_chunk_size=700`. Chiến lược tùy biến bám theo mục và điều của văn bản chính sách, giúp mỗi chunk giữ được ý nghĩa nghiệp vụ rõ ràng.
- **Code snippet (nếu custom):** Xem phần triển khai chiến lược `Policy-section` trong mã nguồn của nhóm.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| 1 | Fixed-small (400, overlap 50) | 10 | Cả 5 câu đều đưa tài liệu liên quan lên top-1; cân bằng tốt giữa độ chính xác và ngữ cảnh | 439 chunk, chi phí lập chỉ mục cao hơn các cấu hình chunk lớn |
| 2 | Fixed-large (800, overlap 120) | 10 | Ít chunk nhất (228), giữ được bối cảnh rộng | Câu 1 đúng ở hạng 3, câu 2 ở hạng 2; top-1 dễ chứa nội dung nhiễu |
| 3 | Sentence-4 | 10 | Cả 5 câu đúng ở top-1; ranh giới chunk tự nhiên | Độ dài chunk biến thiên và có thể lớn với câu/danh sách dài |
| 4 | Recursive-700 | 10 | 4/5 câu đúng ở top-1; số chunk vừa phải (298) | Câu 1 chỉ ở hạng 2 |
| 5 | Policy-section (custom) | 10 | 4/5 câu đúng ở top-1; bảo toàn cấu trúc điều/mục | Nhiều chunk nhất (553); câu 2 chỉ ở hạng 2 |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> `fixed-small` và `sentence-4` cùng đạt 10/10 và đưa tài liệu liên quan lên top-1 ở cả 5 câu. Nhóm chọn `sentence-4` là cấu hình tốt nhất về chất lượng vì giữ ranh giới câu tự nhiên với chỉ 263 chunk, ít hơn đáng kể so với 439 chunk của `fixed-small`; tuy nhiên `fixed-small` an toàn hơn nếu corpus có nhiều danh sách hoặc dòng không kết thúc bằng dấu câu.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua có bao lâu để gửi yêu cầu trả hàng hoặc hoàn tiền sau khi đơn hàng được giao thành công? | Thông thường là 15 ngày; riêng thực phẩm tươi sống và đông lạnh là 24 giờ. | `shopee-return-refund-policy`, mục 3.2 |
| 2 | Người mua bổ sung bằng chứng cho yêu cầu trả hàng hoặc hoàn tiền như thế nào? | Bổ sung đúng hạn; thêm ảnh/video qua thông báo yêu cầu bổ sung hoặc Tôi > Trả hàng/Hoàn tiền. | `shopee-return-review-process`, phần hướng dẫn bổ sung bằng chứng |
| 3 | Người bán phải đáp ứng yêu cầu gì về hình ảnh thật khi đăng sản phẩm trên Shopee? | Có ít nhất một ảnh thật tự chụp; sản phẩm thật chiếm ít nhất 40% diện tích ảnh. | `shopee-product-listing-rules`, khoản b về hình ảnh |
| 4 | Người bán không được đăng bán những nội dung hoặc sản phẩm nào trên Shopee? | Không đăng hàng/nội dung vi phạm pháp luật hoặc chính sách, gồm nhóm cấm/hạn chế và nội dung phản động, khiêu dâm, bạo lực, xúc phạm, rác. | `shopee-product-listing-rules` và `shopee-prohibited-products`, phần nội dung/sản phẩm cấm |
| 5 | Khi tự sắp xếp vận chuyển hàng hoàn trả, chi phí được xử lý như thế nào? | Khách hàng trả trước; nếu yêu cầu được chấp nhận thì được hoàn qua Số Dư Tài Khoản Shopee, hoặc chỉ hỗ trợ một phần bằng Shopee Xu trong trường hợp đổi ý đủ điều kiện. | `shopee-return-shipping-fees`, phần Tự sắp xếp; bắt buộc filter `customer_role=buyer` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn gửi yêu cầu trả hàng/hoàn tiền | Fixed-small, Sentence-4, Policy-section | Có (5/5 cấu hình) | Ba cấu hình này đưa đúng tài liệu lên top-1; Recursive-700 ở hạng 2, Fixed-large ở hạng 3. |
| 2 | Cách bổ sung bằng chứng | Fixed-small, Sentence-4, Recursive-700 | Có (5/5 cấu hình) | Ba cấu hình đạt top-1; Fixed-large và Policy-section đạt hạng 2. |
| 3 | Yêu cầu về ảnh thật của người bán | Fixed-small, Sentence-4, Recursive-700, Policy-section | Có (5/5 cấu hình) | Bốn cấu hình đạt top-1; Fixed-large cũng top-1 sau khi lọc `seller`. |
| 4 | Nội dung/sản phẩm không được đăng bán | Cả 5 cấu hình | Có (5/5 cấu hình) | Tất cả đạt top-1 từ một trong hai tài liệu chuẩn. |
| 5 | Chi phí khi tự sắp xếp hoàn trả | Cả 5 cấu hình | Có (5/5 cấu hình) | Tất cả đạt top-1 với filter `customer_role=buyer`. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có. Tác động rõ nhất xuất hiện ở câu 3: với `fixed-small`, kết quả top-1 không lọc là `shopee-return-refund-policy`, nhưng sau khi lọc `customer_role=seller` thì `shopee-product-listing-rules` lên top-1; với `fixed-large`, top-1 không lọc là `shopee-terms-of-service` và cũng được sửa về đúng tài liệu. Các câu 2 và 5 dùng filter `buyer`, còn câu 4 dùng filter `seller`, giúp giới hạn không gian tìm kiếm đúng vai trò dù tài liệu liên quan vốn đã nằm trong top-3.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> Cả năm cấu hình đều đạt hit top-3 5/5 và điểm truy xuất 10/10, nhưng chất lượng xếp hạng khác nhau; chỉ `fixed-small` và `sentence-4` đạt top-1 cho cả năm câu. Chunk lớn nhất (`fixed-large`, trung bình 786,18 ký tự) có ít chunk nhất nhưng để tài liệu đúng của câu 1 xuống hạng 3 và câu 2 xuống hạng 2. Metadata theo vai trò khách hàng sửa trực tiếp kết quả top-1 sai ở câu 3 đối với hai cấu hình fixed-size.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một corpus và embedding model, kích thước cũng như ranh giới chunk không làm thay đổi hit top-3 trong bộ benchmark nhỏ này nhưng ảnh hưởng rõ đến top-1 và lượng dữ liệu phải lập chỉ mục. Chunk quá lớn giữ được bối cảnh song trộn nhiều chủ đề, còn chia theo câu hoặc fixed-size nhỏ tạo biểu diễn tập trung hơn cho truy vấn chính sách cụ thể.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ mở rộng benchmark với nhiều câu hỏi khó và hard-negative, chấm thêm MRR/nDCG thay vì chỉ dùng hit@3, đồng thời đo thời gian lập chỉ mục và truy vấn. Nhóm cũng sẽ chuẩn hóa `document_version` đang là `not-stated`, bổ sung metadata theo loại chính sách/mục/điều, và thử chiến lược lai `policy-section` với giới hạn độ dài nhỏ hơn hoặc reranker.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
