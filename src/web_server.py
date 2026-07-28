"""Local web server for the OrderCare UI. Run: python src/web_server.py"""

from __future__ import annotations

import json
import re
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from database import create_return_request, get_order, initialize, list_orders, save_message


UI_DIR = Path(__file__).resolve().parents[1] / "ui"
ORDER_PATTERN = re.compile(r"#?([A-Za-z]{2,}\d+)")


def policy(category: str, days: int) -> tuple[bool, str]:
    if days <= 7:
        qualifier = "nếu lỗi từ nhà sản xuất" if category == "Điện tử" else "với điều kiện còn nguyên tem mác"
        return True, f"HỢP LỆ: {category} được hỗ trợ đổi trả trong 7 ngày ({qualifier})."
    return False, f"TỪ CHỐI: Đã giao {days} ngày; chính sách chỉ hỗ trợ đổi trả trong 7 ngày."


def process_message(message: str, mode: str) -> dict:
    save_message("user", message)
    if mode == "baseline":
        answer = "Tôi không thể xác minh dữ liệu đơn hàng hoặc thực hiện thao tác thực tế ở chế độ Chatbot Baseline. Vui lòng dùng ReAct Agent hoặc liên hệ CSKH."
        save_message("assistant", answer)
        return {"answer": answer, "trace": [], "order": None, "mode": "baseline"}

    match = ORDER_PATTERN.search(message)
    if not match:
        answer = "Vui lòng cung cấp mã đơn hàng, ví dụ #DH1004, để tôi có thể tra cứu."
        save_message("assistant", answer)
        return {"answer": answer, "trace": [], "order": None, "mode": "react"}

    order_id = match.group(1).upper()
    trace = [{"kind": "Thought", "text": "Tôi cần tra cứu thông tin đơn hàng trước khi trả lời."}]
    order = get_order(order_id)
    trace.append({"kind": "Action", "text": f"lookup_order({order_id})"})
    if not order:
        trace.append({"kind": "Observation", "text": f"LỖI: Không tìm thấy đơn hàng {order_id}."})
        answer = "Tôi chưa tìm thấy đơn hàng này. Vui lòng kiểm tra lại mã đơn hoặc liên hệ CSKH."
        save_message("assistant", answer)
        return {"answer": answer, "trace": trace, "order": None, "mode": "react"}

    trace.append({"kind": "Observation", "text": f"{order['status']} · {order['product']} · {order['delivery_days_ago']} ngày từ khi giao."})
    text = message.lower()
    if any(word in text for word in ("đổi", "trả", "hoàn tiền", "refund")):
        trace.extend([
            {"kind": "Thought", "text": "Tôi cần kiểm tra điều kiện đổi trả của đơn hàng."},
            {"kind": "Action", "text": f"check_return_policy({order['category']}, {order['delivery_days_ago']})"},
        ])
        eligible, result = policy(order["category"], order["delivery_days_ago"])
        trace.append({"kind": "Observation", "text": result})
        if not eligible:
            save_message("assistant", result)
            return {"answer": result, "trace": trace, "order": order, "mode": "react"}
        request = create_return_request(order_id, "Yêu cầu đổi/trả từ khách hàng")
        trace.extend([
            {"kind": "Thought", "text": "Đơn hàng đủ điều kiện; tôi sẽ tạo yêu cầu đổi trả."},
            {"kind": "Action", "text": f"create_return_request({order_id})"},
            {"kind": "Observation", "text": f"Đã tạo phiếu {request['request_id']}."},
        ])
        answer = f"Đã tạo phiếu đổi trả {request['request_id']}. Shipper sẽ liên hệ lấy hàng trong 24 giờ tới."
    else:
        answer = f"Đơn {order['order_id']} đang ở trạng thái: {order['status']}. {order['delivery_note']}."

    save_message("assistant", answer)
    return {"answer": answer, "trace": trace, "order": order, "mode": "react"}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(UI_DIR), **kwargs)

    def send_json(self, payload: object, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/orders":
            return self.send_json(list_orders())
        if path.startswith("/api/orders/"):
            order = get_order(path.rsplit("/", 1)[-1])
            return self.send_json(order or {"error": "Không tìm thấy đơn hàng"}, HTTPStatus.OK if order else HTTPStatus.NOT_FOUND)
        if path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if urlparse(self.path).path != "/api/chat":
            return self.send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8-sig"))
            message = str(payload.get("message", "")).strip()
            mode = str(payload.get("mode", "react"))
            if not message:
                return self.send_json({"error": "Vui lòng nhập câu hỏi"}, HTTPStatus.BAD_REQUEST)
            return self.send_json(process_message(message, mode))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self.send_json({"error": "Dữ liệu không hợp lệ"}, HTTPStatus.BAD_REQUEST)


if __name__ == "__main__":
    initialize()
    print("OrderCare UI: http://localhost:8000")
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
