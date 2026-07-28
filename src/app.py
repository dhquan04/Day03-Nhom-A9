"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import re
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import (
    check_return_policy,
    create_return_request,
    lookup_order,
)
from prompts import CHATBOT_BASELINE_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


def run_react_agent(user_query: str, provider):
    """
    Chạy luồng ReAct cho tra cứu đơn hàng và xử lý đổi trả.

    Phiên bản lab này dùng các luật định tuyến đơn giản để chọn tool; mọi thao tác
    đều được ghi theo định dạng Thought -> Action -> Observation.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    normalized_query = user_query.lower()
    order_match = re.search(r"#?([a-z]{2,}\d+)", user_query, re.IGNORECASE)

    if not order_match:
        print("🏁 Final Answer: Vui lòng cung cấp mã đơn hàng để tôi có thể kiểm tra.")
        return

    order_id = order_match.group(1).upper()
    print("\n--- 🔄 Vòng lặp ReAct (Step 1/{}) ---".format(MAX_ITERATIONS))
    print("🧠 Thought: Tôi cần tra cứu thông tin đơn hàng trước khi trả lời.")
    print(f"🛠️ Action: lookup_order['{order_id}']")
    order_observation = lookup_order(order_id)
    print(f"👁️ Observation: {order_observation}")

    if order_observation.startswith("LỖI:"):
        print("🏁 Final Answer: Tôi chưa tìm thấy đơn hàng này. Vui lòng kiểm tra lại mã đơn hàng hoặc liên hệ chăm sóc khách hàng.")
        return

    is_return_request = any(
        keyword in normalized_query
        for keyword in ("đổi", "trả", "hoàn tiền", "refund")
    )
    if not is_return_request:
        print(f"🏁 Final Answer: {order_observation}")
        return

    category_match = re.search(r"Danh mục: ([^|]+)", order_observation)
    days_match = re.search(r"Đã giao: (\d+) ngày", order_observation)
    if not category_match or not days_match:
        print("🏁 Final Answer: Đơn hàng chưa có đủ thông tin giao nhận để xử lý yêu cầu đổi trả.")
        return

    print("\n--- 🔄 Vòng lặp ReAct (Step 2/{}) ---".format(MAX_ITERATIONS))
    category = category_match.group(1).strip()
    days_since_delivery = int(days_match.group(1))
    print("🧠 Thought: Tôi cần kiểm tra đơn hàng có còn trong thời hạn đổi trả hay không.")
    print(f"🛠️ Action: check_return_policy['{category}', {days_since_delivery}]")
    policy_observation = check_return_policy(category, days_since_delivery)
    print(f"👁️ Observation: {policy_observation}")

    if not policy_observation.startswith("HỢP LỆ"):
        print(f"🏁 Final Answer: {policy_observation}")
        return

    print("\n--- 🔄 Vòng lặp ReAct (Step 3/{}) ---".format(MAX_ITERATIONS))
    print("🧠 Thought: Đơn hàng đủ điều kiện, tôi sẽ tạo yêu cầu đổi trả.")
    print(f"🛠️ Action: create_return_request['{order_id}', 'Yêu cầu từ khách hàng']")
    return_observation = create_return_request(order_id, "Yêu cầu từ khách hàng")
    print(f"👁️ Observation: {return_observation}")
    print(f"🏁 Final Answer: {return_observation}")


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
    # Each baseline case makes one LLM call and never invokes a tool.
    for test_case in tests:
        print(f"\n[Test case #{test_case['id']}]")
        run_baseline_chatbot(test_case["question"], provider)

    # Dùng case đổi size để trình diễn đủ luồng tra cứu -> kiểm tra chính sách
    # -> tạo phiếu đổi trả với các tool trong tools.py.
    sample_query = tests[3]["question"]
    
    print("\n--- DEMO 2: CHẠY TRÊN REACT AGENT ---")
    run_react_agent(sample_query, provider)
