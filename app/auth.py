"""CP3 — Xác thực bằng API key.

Public URL = ai cũng gọi được. Không có lớp này, hóa đơn LLM của bạn do
người lạ quyết định.
"""

from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, status

from .config import get_settings

ANONYMOUS_USER = "anonymous"


def verify_api_key(
    x_api_key: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
) -> str:
    """Kiểm tra header ``X-API-Key``; trả về user_id nếu hợp lệ.

    So sánh bằng compare_digest để không để lộ vị trí ký tự không khớp qua
    thời gian phản hồi. API key được kỳ vọng là ASCII, nhưng encode đầu vào
    giúp một header Unicode không hợp lệ cũng nhận 401 thay vì 500.
    """
    expected_key = get_settings().agent_api_key
    supplied_key = x_api_key or ""
    if not secrets.compare_digest(
        supplied_key.encode("utf-8"), expected_key.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing API key",
        )

    return x_user_id or ANONYMOUS_USER
