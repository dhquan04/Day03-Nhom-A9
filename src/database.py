"""SQLite persistence for the OrderCare demo application."""

from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "ordercare.db"

SEED_ORDERS = (
    ("DH1001", "Bộ nén cà phê Espresso Stainless", "Gia dụng", "Đang vận chuyển", 0, 450000, "Dự kiến giao ngày mai", "Đã thanh toán"),
    ("DH1002", "Bàn phím cơ không dây K6", "Điện tử", "Đã xác nhận thanh toán", 1, 1850000, "Đang chuẩn bị hàng", "Đã thanh toán"),
    ("DH1003", "Áo thun Basic x2, Quần jeans Slim Fit x1", "Thời trang", "Đã giao", 5, 1050000, "Đã giao thành công", "Đã thanh toán"),
    ("DH1004", "Áo khoác Blazer công sở (Size M)", "Thời trang", "Đã giao", 2, 650000, "Đã giao thành công", "Đã thanh toán"),
    ("DH1005", "Váy Linen (lỗi rách đường may)", "Thời trang", "Đã giao", 2, 680000, "Đã giao thành công", "Đã thanh toán"),
    ("DH1006", "Giày thể thao Sneaker RunFast", "Thời trang", "Đang chuẩn bị hàng", 0, 850000, "Chưa bàn giao vận chuyển", "Đã thanh toán"),
    ("DH8888", "Loa Bluetooth BassBoost Pro", "Điện tử", "Đã giao", 240, 2500000, "Đã giao thành công", "Đã thanh toán"),
)


def connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize() -> None:
    with connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                product TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL,
                delivery_days_ago INTEGER NOT NULL,
                total_amount INTEGER NOT NULL,
                delivery_note TEXT NOT NULL,
                payment_status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS return_requests (
                request_id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Đang tiếp nhận',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
            );
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.executemany(
            """
            INSERT OR IGNORE INTO orders
            (order_id, product, category, status, delivery_days_ago, total_amount, delivery_note, payment_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            SEED_ORDERS,
        )


def get_order(order_id: str) -> dict | None:
    initialize()
    clean_id = order_id.strip().upper().replace("#", "")
    with connection() as conn:
        row = conn.execute("SELECT * FROM orders WHERE order_id = ?", (clean_id,)).fetchone()
    return dict(row) if row else None


def list_orders() -> list[dict]:
    initialize()
    with connection() as conn:
        rows = conn.execute("SELECT * FROM orders ORDER BY order_id").fetchall()
    return [dict(row) for row in rows]


def create_return_request(order_id: str, reason: str) -> dict:
    initialize()
    clean_id = order_id.strip().upper().replace("#", "")
    request_id = f"RET-{clean_id}-2026"
    with connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO return_requests (request_id, order_id, reason)
            VALUES (?, ?, ?)
            """,
            (request_id, clean_id, reason),
        )
        row = conn.execute("SELECT * FROM return_requests WHERE request_id = ?", (request_id,)).fetchone()
    return dict(row)


def save_message(role: str, content: str) -> None:
    initialize()
    with connection() as conn:
        conn.execute("INSERT INTO conversations (role, content) VALUES (?, ?)", (role, content))
