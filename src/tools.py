"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo và xử lý phòng thủ (Safeguards & Crash-proof) cho các công cụ của ReAct Agent trong Mốc 3.
"""

from typing import Union, Any, Dict


def lookup_order(order_id: str) -> str:
    """
    Tra cứu thông tin chi tiết của một đơn hàng dựa trên mã đơn.
    
    Args:
        order_id (str): Mã đơn hàng (Ví dụ: 'ORD123', 'ORD456', 'ORD789', '#DH1001')
        
    Returns:
        str: Chi tiết sản phẩm, ngày giao hàng, trạng thái đơn hàng hoặc thông báo lỗi.
    """
    try:
        if not order_id or not isinstance(order_id, str):
            return "LỖI: Mã đơn hàng không hợp lệ hoặc bị để trống."
            
        clean_id = str(order_id).strip().upper().replace("#", "")
        
        # Cơ sở dữ liệu mẫu mở rộng phục vụ bộ 12 test cases
        orders_db: Dict[str, Dict[str, Any]] = {
            "ORD123": {
                "product": "Áo sơ mi nam Oxford (Size L)",
                "category": "Thời trang",
                "status": "Đã giao",
                "delivery_days_ago": 3,
                "price": "350,000 VNĐ"
            },
            "ORD456": {
                "product": "Tai nghe Bluetooth Wireless X",
                "category": "Điện tử",
                "status": "Đã giao",
                "delivery_days_ago": 15,
                "price": "1,200,000 VNĐ"
            },
            "ORD789": {
                "product": "Giày thể thao Sneaker RunFast",
                "category": "Thời trang",
                "status": "Đang vận chuyển",
                "delivery_days_ago": 0,
                "price": "850,000 VNĐ"
            },
            "DH1001": {
                "product": "Bộ nén cà phê Espresso Stainless",
                "category": "Gia dụng",
                "status": "Đang vận chuyển",
                "delivery_days_ago": 0,
                "price": "450,000 VNĐ"
            },
            "DH1002": {
                "product": "Bàn phím cơ không dây K6",
                "category": "Điện tử",
                "status": "Đã xác nhận thanh toán",
                "delivery_days_ago": 1,
                "price": "1,850,000 VNĐ"
            },
            "DH1004": {
                "product": "Áo khoác Blazer công sở (Size M)",
                "category": "Thời trang",
                "status": "Đã giao",
                "delivery_days_ago": 2,
                "price": "650,000 VNĐ"
            },
            "DH8888": {
                "product": "Loa Bluetooth BassBoost Pro",
                "category": "Điện tử",
                "status": "Đã giao",
                "delivery_days_ago": 240,
                "price": "2,500,000 VNĐ"
            }
        }
        
        if clean_id in orders_db:
            info = orders_db[clean_id]
            return (
                f"Mã đơn: {clean_id} | Sản phẩm: {info['product']} | "
                f"Danh mục: {info['category']} | Trạng thái: {info['status']} | "
                f"Đã giao: {info['delivery_days_ago']} ngày trước | Giá: {info['price']}"
            )
        else:
            return f"LỖI: Không tìm thấy đơn hàng với mã '{order_id}'. Vui lòng kiểm tra lại mã đơn."
            
    except Exception as e:
        return f"LỖI HỆ THỐNG: Xảy ra lỗi khi tra cứu đơn hàng '{order_id}': {str(e)}"


def check_return_policy(category: str, days_since_delivery: Union[int, str]) -> str:
    """
    Kiểm tra xem sản phẩm có đủ điều kiện đổi trả theo chính sách hay không.
    
    Args:
        category (str): Ngành hàng ('Thời trang', 'Điện tử', 'Gia dụng')
        days_since_delivery (int/str): Số ngày kể từ khi nhận hàng
        
    Returns:
        str: Kết quả kiểm tra chính sách đổi trả hoặc thông báo lỗi.
    """
    try:
        if days_since_delivery is None:
            return "LỖI: Số ngày nhận hàng không được để trống."
            
        days = int(days_since_delivery)
        cat_lower = str(category).lower() if category else ""
        
        if "thời trang" in cat_lower:
            if days <= 7:
                return "HỢP LỆ: Ngành Thời trang được hỗ trợ đổi trả trong 7 ngày (yêu cầu nguyên tem mác)."
            else:
                return f"TỪ CHỐI: Đã giao {days} ngày. Ngành Thời trang chỉ hỗ trợ đổi trả trong tối đa 7 ngày."
        elif "điện tử" in cat_lower:
            if days <= 7:
                return "HỢP LỆ: Ngành Điện tử được hỗ trợ đổi trả trong 7 ngày nếu lỗi từ nhà sản xuất."
            else:
                return f"TỪ CHỐI: Đã giao {days} ngày. Ngành Điện tử chỉ hỗ trợ đổi trả trong 7 ngày đầu."
        else:
            if days <= 7:
                return "HỢP LỆ: Sản phẩm đủ điều kiện xét đổi trả trong vòng 7 ngày."
            else:
                return f"TỪ CHỐI: Sản phẩm đã giao {days} ngày, vượt quá thời hạn 7 ngày quy định."
                
    except (ValueError, TypeError):
        return f"LỖI THAM SỐ: Số ngày giao hàng '{days_since_delivery}' không hợp lệ (bắt buộc là số nguyên)."
    except Exception as e:
        return f"LỖI HỆ THỐNG: Không thể kiểm tra chính sách đổi trả: {str(e)}"


def create_return_request(order_id: str, reason: str) -> str:
    """
    Tạo yêu cầu/mã phiếu đổi trả cho đơn hàng đủ điều kiện.
    
    Args:
        order_id (str): Mã đơn hàng
        reason (str): Lý do đổi trả (VD: 'Chật size', 'Sản phẩm lỗi')
        
    Returns:
        str: Thông báo tạo mã phiếu đổi trả thành công hoặc thông báo lỗi.
    """
    try:
        if not order_id:
            return "LỖI: Thiếu mã đơn hàng để tạo phiếu đổi trả."
        if not reason:
            return "LỖI: Vui lòng cung cấp lý do đổi trả sản phẩm."
            
        clean_id = str(order_id).strip().upper().replace("#", "")
        return (
            f"✅ TẠO PHIẾU ĐỔI TRẢ THÀNH CÔNG!\n"
            f"- Mã đơn hàng: {clean_id}\n"
            f"- Mã phiếu đổi trả: RET-{clean_id}-2026\n"
            f"- Lý do: {reason}\n"
            f"- Hướng dẫn: Đóng gói sản phẩm và dán mã RET-{clean_id}-2026 lên bưu kiện. "
            f"Shipper sẽ đến lấy trong 24h tới."
        )
    except Exception as e:
        return f"LỖI HỆ THỐNG: Không thể tạo phiếu đổi trả cho đơn '{order_id}': {str(e)}"


def execute_tool(tool_name: str, **kwargs) -> str:
    """
    Hàm wrapper an toàn giúp ReAct Agent gọi bất kỳ công cụ nào mà không sợ crash ứng dụng.
    """
    if tool_name not in AVAILABLE_TOOLS:
        return f"LỖI: Công cụ '{tool_name}' không tồn tại. Các công cụ khả dụng: {list(AVAILABLE_TOOLS.keys())}"
    try:
        tool_fn = AVAILABLE_TOOLS[tool_name]
        return tool_fn(**kwargs)
    except Exception as e:
        return f"LỖI THỰC THI TOOL '{tool_name}': {str(e)}"


def get_tools_description() -> str:
    """Trả về mô tả các công cụ dạng văn bản cho System Prompt của ReAct Agent"""
    return (
        "1. lookup_order[order_id]: Tra cứu thông tin đơn hàng, trạng thái, ngày giao hàng.\n"
        "2. check_return_policy[category, days_since_delivery]: Kiểm tra xem đơn hàng thuộc ngành hàng đó có được đổi trả không.\n"
        "3. create_return_request[order_id, reason]: Khởi tạo phiếu và cấp mã đổi trả hàng."
    )


# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "lookup_order": lookup_order,
    "check_return_policy": check_return_policy,
    "create_return_request": create_return_request,
}
