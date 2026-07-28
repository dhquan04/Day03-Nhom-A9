# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer*
*Chủ đề chọn: Đề tài 5 - Trợ Lý Tra Cứu Đơn Hàng & Xử Lý Đổi Trả*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX) - MỐC 1

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `5/5` | Cần suy luận đa bước: Tiếp nhận mã đơn ➔ Tra cứu trạng thái ➔ Đánh giá chính sách đổi trả (thời hạn, tình trạng hàng, lý do) ➔ Đưa ra quyết định/hướng dẫn. |
| 🛠️ **Tool Interaction** | `5/5` | Bắt buộc dùng công cụ tra cứu dữ liệu thời gian thực: Database đơn hàng (`lookup_order`), chính sách đổi trả (`check_return_policy`), hệ thống tạo yêu cầu (`create_return_request`). Chatbot thường không thể truy cập DB này. |
| 🔀 **Dynamic Decision** | `4/5` | Ra quyết định động theo nhánh: Nếu đơn đủ điều kiện ➔ Tạo mã đổi trả; Nếu quá hạn/lỗi khách hàng ➔ Từ chối & giải thích chính sách; Nếu thiếu thông tin ➔ Hỏi bổ sung. |
| ⏳ **Long Horizon** | `4/5` | Quy trình gồm 3–5 bước tương tác khép kín từ lúc khách hỏi đơn đến khi chốt phương án đổi trả/hoàn tiền. |
| **TỔNG ĐIỂM FIT** | **18/20** | **KẾT LUẬN: BÀI TOÁN RẤT HOÀN HẢO ĐỂ ÁP DỤNG REACT AGENT!** |

---

## 🔍 2. KẾT QUẢ CHATBOT BASELINE — 12 TEST CASE

**Cách chạy:** `python src/app.py` với `GeminiProvider`. Mỗi case của Baseline chỉ gọi LLM một lần và không gọi tool.

| Case | Nhu cầu kiểm tra | Kết quả Baseline | Phân loại Role 5 | Nhận xét |
| :---: | :--- | :--- | :--- | :--- |
| #1 | Thời hạn đổi trả | Từ chối cung cấp số ngày chính xác, nhưng tự nêu khoảng 7–30 ngày. | Hallucinated | Mốc 7–30 ngày không có bằng chứng từ chính sách của shop. |
| #2 | Phương thức hoàn tiền | Nêu chuyển khoản, hoàn về phương thức ban đầu, voucher và thời gian 3–7 ngày. | Hallucinated | Đây là quy trình chung do LLM suy đoán, không phải policy đã được tool xác minh. |
| #3 | Điều kiện đổi trả | Nêu thời hạn, tình trạng hàng, tem mác, hóa đơn và lý do hợp lệ. | Hallucinated | Các điều kiện/mốc thời gian chỉ là tham khảo chung, không grounded vào dữ liệu dự án. |
| #4 | Địa chỉ nhận trả trực tiếp | Không cung cấp địa chỉ; hướng dẫn liên hệ CSKH. | Safe fallback | Không bịa địa chỉ hay khẳng định có dữ liệu hệ thống. |
| #5 | Tra cứu trạng thái `DH1001` | Nêu không có quyền tra cứu trạng thái và ngày giao. | Safe fallback | Đúng giới hạn của chatbot không có `lookup_order`. |
| #6 | Kiểm tra thanh toán `DH1002` | Từ chối tra cứu; gợi ý kiểm tra email/SMS hoặc liên hệ CSKH. | Safe fallback | Không khẳng định thanh toán đã thành công. |
| #7 | Danh sách hàng/tổng tiền `DH1003` | Từ chối hiển thị chi tiết; hướng dẫn kiểm tra email/SMS hoặc CSKH. | Safe fallback | Không bịa sản phẩm hoặc tổng tiền. |
| #8 | Đổi size và tạo phiếu `DH1004` | Không kiểm tra kho hay tạo phiếu; gợi ý liên hệ CSKH và giữ nguyên tem mác. | Safe fallback | Không khẳng định đã thực hiện action; lưu ý tem mác chỉ nên xem là hướng dẫn chung. |
| #9 | Hoàn tiền `DH1005` lỗi đường may | Không tạo ticket, nhưng nói shop “luôn” hỗ trợ hoàn tiền 100%. | Hallucinated | Cam kết hoàn tiền 100% không có evidence từ chính sách hoặc tool. |
| #10 | Hủy đơn `DH1006` | Không kiểm tra/hủy đơn; hướng dẫn liên hệ CSKH ngay. | Safe fallback | Không khẳng định đơn chưa giao hoặc đã bị hủy. |
| #11 | Mã không tồn tại `DH9999999` | Không tra cứu được; gợi ý kiểm tra SMS/email và liên hệ CSKH. | Hallucinated / chưa tối ưu | Không bịa vị trí, nhưng giả định đơn có thể đã được gửi đi thay vì xử lý mã không tồn tại bằng tool error. |
| #12 | Trả hàng quá hạn `DH8888` | Gemini trả lỗi `429 RESOURCE_EXHAUSTED` do vượt quota. | System error | Không có phản hồi để đánh giá; cần retry sau thời gian báo bởi API hoặc dùng provider/mock khác. |

### Kết luận quan sát

- Baseline giữ đúng giới hạn **0 tool call**, nên không thể xác minh đơn hàng hay thực hiện đổi/trả/hoàn tiền/hủy đơn.
- Có **6 safe fallback** (#4–#8, #10; trong đó #8 có lưu ý chung) và các case tra cứu đơn (#5–#7, #10) không khẳng định đã làm action.
- Có rủi ro **hallucination** ở #1, #2, #3, #9 và #11 do tự nêu hoặc ngầm giả định chính sách/trạng thái không có evidence.
- Case #12 là lỗi quota của provider, không phải lỗi suy luận của chatbot. Khi chạy đủ 12 case với Gemini free tier, cần có cơ chế retry/backoff hoặc giảm tốc độ gọi.
- ReAct Agent là cần thiết cho các yêu cầu phụ thuộc dữ liệu thật: tra cứu mã đơn, kiểm tra điều kiện đổi trả, tạo phiếu hoàn tiền và hủy đơn.

---

## 🔄 3. REACT TRACE LOGS — MỐC 3

### Case #8 — Đổi size đơn `DH1004` (thành công)

```text
Thought: Tôi cần tra cứu thông tin đơn hàng trước khi trả lời hoặc thực hiện thao tác.
Action: lookup_order[order_id='DH1004']
Observation: Mã đơn: DH1004 | Sản phẩm: Áo khoác Blazer công sở (Size M) |
Danh mục: Thời trang | Trạng thái: Đã giao | Đã giao: 2 ngày trước | Giá: 650,000 VNĐ

Thought: Tôi cần kiểm tra đơn hàng có còn trong thời hạn đổi trả hay không.
Action: check_return_policy[category='Thời trang', days_since_delivery=2]
Observation: HỢP LỆ: Ngành Thời trang được hỗ trợ đổi trả trong 7 ngày
(yêu cầu nguyên tem mác).

Thought: Đơn hàng đủ điều kiện; tôi sẽ tạo phiếu đổi trả.
Action: create_return_request[order_id='DH1004', reason='Đổi/trả theo yêu cầu của khách hàng']
Observation: ✅ TẠO PHIẾU ĐỔI TRẢ THÀNH CÔNG!
Mã phiếu đổi trả: RET-DH1004-2026

Final Answer: Phiếu đổi trả RET-DH1004-2026 đã được tạo thành công.
```

**Đánh giá:** Agent chọn đúng 3 tool theo thứ tự, dùng Observation làm bằng chứng và dừng sau bước thứ 3.

### Case #12 — Đơn `DH8888` trả hàng quá hạn (guardrail)

```text
Thought: Tôi cần tra cứu thông tin đơn hàng trước khi trả lời hoặc thực hiện thao tác.
Action: lookup_order[order_id='DH8888']
Observation: Mã đơn: DH8888 | Sản phẩm: Loa Bluetooth BassBoost Pro |
Danh mục: Điện tử | Trạng thái: Đã giao | Đã giao: 240 ngày trước | Giá: 2,500,000 VNĐ

Thought: Tôi cần kiểm tra đơn hàng có còn trong thời hạn đổi trả hay không.
Action: check_return_policy[category='Điện tử', days_since_delivery=240]
Observation: TỪ CHỐI: Đã giao 240 ngày. Ngành Điện tử chỉ hỗ trợ đổi trả trong 7 ngày đầu.

Final Answer: TỪ CHỐI: Đã giao 240 ngày. Ngành Điện tử chỉ hỗ trợ đổi trả trong 7 ngày đầu.
```

**Đánh giá:** Guardrail hoạt động đúng: Agent không gọi `create_return_request` khi policy từ chối.

### Case #11 — Mã đơn không tồn tại `DH9999999` (guardrail)

```text
Thought: Tôi cần tra cứu thông tin đơn hàng trước khi trả lời hoặc thực hiện thao tác.
Action: lookup_order[order_id='DH9999999']
Observation: LỖI: Không tìm thấy đơn hàng với mã 'DH9999999'. Vui lòng kiểm tra lại mã đơn.

Final Answer: Tôi chưa tìm thấy đơn hàng này. Vui lòng kiểm tra lại mã đơn hàng
hoặc liên hệ bộ phận chăm sóc khách hàng.
```

**Đánh giá:** Agent dừng ngay sau Observation lỗi; không tiếp tục gọi chính sách đổi trả hoặc tạo phiếu.
