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
    execute_tool,
)
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
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
    Chạy ReAct Agent theo luồng Thought -> Action -> Observation có guardrail.

    Agent chỉ gọi tool thông qua execute_tool(), nên lỗi từ tool được trả về dưới
    dạng Observation thay vì làm crash ứng dụng.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    if not REACT_SYSTEM_PROMPT.strip():
        print("🏁 Final Answer: ReAct system prompt chưa được cấu hình.")
        return {"answer": "ReAct system prompt chưa được cấu hình.", "trace": []}
    print(f"⚙️ ReAct Prompt đã nạp với tối đa {MAX_ITERATIONS} bước.")
    normalized_query = user_query.lower()
    order_match = re.search(r"#?([a-z]{2,}\d+)", user_query, re.IGNORECASE)
    trace = []

    def log_step(step, thought, action=None, observation=None):
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        print(f"🧠 Thought: {thought}")
        if action:
            print(f"🛠️ Action: {action}")
        if observation is not None:
            print(f"👁️ Observation: {observation}")
        trace.append({
            "step": step,
            "thought": thought,
            "action": action,
            "observation": observation,
        })

    def finish(answer):
        print("🧠 Thought: Tôi đã có đủ thông tin để trả lời an toàn.")
        print(f"🏁 Final Answer: {answer}")
        return {"answer": answer, "trace": trace}

    if not order_match:
        return finish("Vui lòng cung cấp mã đơn hàng để tôi có thể kiểm tra.")

    order_id = order_match.group(1).upper()
    order_action = f"lookup_order[order_id='{order_id}']"
    order_observation = execute_tool("lookup_order", order_id=order_id)
    log_step(
        1,
        "Tôi cần tra cứu thông tin đơn hàng trước khi trả lời hoặc thực hiện thao tác.",
        order_action,
        order_observation,
    )

    if order_observation.startswith("LỖI"):
        return finish(
            "Tôi chưa tìm thấy đơn hàng này. Vui lòng kiểm tra lại mã đơn hàng "
            "hoặc liên hệ bộ phận chăm sóc khách hàng."
        )

    if "hủy" in normalized_query:
        return finish(
            "Tôi đã tra cứu được đơn hàng, nhưng phiên bản lab hiện chưa đăng ký tool "
            "hủy đơn. Vui lòng liên hệ chăm sóc khách hàng để được hỗ trợ kịp thời."
        )

    if "hoàn tiền" in normalized_query or "refund" in normalized_query:
        return finish(
            "Tôi đã tra cứu được đơn hàng, nhưng phiên bản lab hiện chưa đăng ký tool "
            "tạo ticket hoàn tiền. Vui lòng liên hệ chăm sóc khách hàng kèm ảnh/video sản phẩm lỗi."
        )

    is_return_request = any(
        keyword in normalized_query
        for keyword in ("đổi", "trả", "hoàn tiền", "refund")
    )
    if not is_return_request:
        return finish(order_observation)

    category_match = re.search(r"Danh mục: ([^|]+)", order_observation)
    days_match = re.search(r"Đã giao: (\d+) ngày", order_observation)
    if not category_match or not days_match:
        return finish("Đơn hàng chưa có đủ thông tin giao nhận để xử lý yêu cầu đổi trả.")

    category = category_match.group(1).strip()
    days_since_delivery = int(days_match.group(1))
    policy_action = (
        "check_return_policy["
        f"category='{category}', days_since_delivery={days_since_delivery}]"
    )
    policy_observation = execute_tool(
        "check_return_policy",
        category=category,
        days_since_delivery=days_since_delivery,
    )
    log_step(
        2,
        "Tôi cần kiểm tra đơn hàng có còn trong thời hạn đổi trả hay không.",
        policy_action,
        policy_observation,
    )

    if not policy_observation.startswith("HỢP LỆ"):
        return finish(policy_observation)

    reason = "Đổi/trả theo yêu cầu của khách hàng"
    return_action = f"create_return_request[order_id='{order_id}', reason='{reason}']"
    return_observation = execute_tool(
        "create_return_request",
        order_id=order_id,
        reason=reason,
    )
    log_step(
        3,
        "Đơn hàng đủ điều kiện; tôi sẽ tạo phiếu đổi trả.",
        return_action,
        return_observation,
    )

    if return_observation.startswith("LỖI"):
        return finish("Không thể tạo phiếu đổi trả lúc này. Vui lòng thử lại hoặc liên hệ chăm sóc khách hàng.")
    return finish(return_observation)


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
