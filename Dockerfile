# ═══════════════════════════════════════════════════════════════════
# CP2 — Containerization
#
# Builder cài dependency; runtime dùng image slim và chạy bằng appuser.
#
# Các yêu cầu đã triển khai:
#   [x] Multi-stage build: stage `builder` cài dependency, stage runtime
#       chỉ copy kết quả sang → image nhỏ hơn, không mang theo compiler.
#       Cú pháp: `FROM python:3.11-slim AS builder`
#   [x] Base image slim (hoặc alpine), không dùng `python:3.11` bản đầy đủ
#   [x] COPY requirements.txt và pip install TRƯỚC khi COPY source code
#       (Docker cache theo layer: sửa 1 dòng code không phải cài lại thư viện)
#   [x] Tạo user thường và chuyển sang bằng lệnh `USER`
#   [x] Có `HEALTHCHECK` gọi vào endpoint /health
#   [x] Đọc cổng từ biến môi trường PORT (cloud tự gán cổng, không cố định 8000)
#
# Kiểm tra:  pytest tests/test_cp2.py -v
# Build thử: docker build -t day12-agent:prod .
#            docker images day12-agent:prod     # xem dung lượng
# ═══════════════════════════════════════════════════════════════════

FROM python:3.11-slim AS builder

WORKDIR /build

# Cache dependencies separately from application code.
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=120 --retries=5 --prefix=/install -r requirements.txt

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

COPY --from=builder /install /usr/local
RUN useradd --create-home --uid 10001 appuser

COPY app ./app
COPY utils ./utils

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/health', timeout=3).read()"

# exec lets uvicorn receive Docker's shutdown signals directly.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
