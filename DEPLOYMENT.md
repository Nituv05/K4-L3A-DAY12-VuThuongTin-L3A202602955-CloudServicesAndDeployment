# Thông Tin Deploy — Checkpoint 5

> Điền file này sau khi deploy xong. `pytest tests/test_cp5.py` đọc file này
> để tìm địa chỉ service của bạn và gọi thử.
>
> **Chỉ ghi TÊN biến môi trường, tuyệt đối không dán giá trị API key vào đây.**
> Repo này công khai — dán khóa vào là mất khóa.

## Thông Tin Học Viên

| Mục | Nội dung |
|-----|----------|
| Họ và tên | Vũ Thường Tín |
| Mã học viên | 2A202602955 |
| Repo | https://github.com/Nituv05/K4-L3A-DAY12-VuThuongTin-L3A202602955-CloudServicesAndDeployment |

## Service

| Mục | Nội dung |
|-----|----------|
| Public URL | https://day12-agent-4n9z.onrender.com |
| Platform | Render |
| Ngày deploy | 2026-09-28 |

## Biến Môi Trường Đã Set Trên Cloud

Ghi tên biến và **nguồn giá trị**, không ghi giá trị:

| Biến | Đã set | Ghi chú |
|------|--------|---------|
| `PORT` | ✅ | platform tự gán |
| `AGENT_API_KEY` | ✅ | đặt trong dashboard, không nằm trong repo |
| `REDIS_URL` | ✅ | Render Key Value day12-redis, region Oregon; Blueprint gán connectionString |
| `RATE_LIMIT_PER_MINUTE` | ✅ | 10 |
| `MONTHLY_BUDGET_USD` | ✅ | 10.0 |
| `LOG_LEVEL` | ✅ | INFO |

## Lệnh Kiểm Tra

Thay `<URL>` bằng Public URL ở trên:

```bash
# 1. Liveness — mong đợi 200 {"status":"ok"}
curl -i <URL>/health

# 2. Readiness — mong đợi 200 {"status":"ready"} (đã nối được Redis)
curl -i <URL>/ready

# 3. Không có API key — mong đợi 401
curl -i -X POST <URL>/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello"}'

# 4. Có API key — mong đợi 200 kèm câu trả lời
curl -i -X POST <URL>/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $AGENT_API_KEY" \
  -H "X-User-Id: sv-test" \
  -d '{"question":"Deploy là gì?"}'

# 5. Rate limit — gọi 15 lần, những lần cuối phải trả 429
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code} " -X POST <URL>/ask \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $AGENT_API_KEY" \
    -H "X-User-Id: sv-test" \
    -d '{"question":"test"}'
done; echo
```

## Kết Quả Chạy Thật

Dán output của các lệnh trên vào đây:

```
Kiểm tra thật ngày 2026-09-28:
GET /health → 200 {"status":"ok","service":"day12-agent","version":"1.0.0"}
GET /ready → 200 {"status":"ready","redis":true}
POST /ask không có khóa → 401 {"detail":"invalid or missing API key"}
POST /ask có khóa → 200; answer có nội dung; history_length=0; cost_usd=0.00002145
15 request tuần tự với user mới → 200 200 200 200 200 200 200 200 200 200 429 429 429 429 429
CP1–CP5: 79 passed, 4 skipped (fallback local), không có test fail.
```

## Ảnh Chụp Màn Hình

Đặt ảnh trong thư mục `screenshots/`:

- `screenshots/dashboard.png` — ảnh dashboard học viên cung cấp lúc 23:12 ngày 2026-09-28: day12-agent có trạng thái Deployed và day12-redis có trạng thái Available, cùng region Oregon
- `screenshots/health.png` — ảnh trình duyệt headless gọi /health trên URL public sau khi sửa lỗi; response status ok

---

## Lỗi Deploy Đã Xử Lý

Lần đầu tạo thêm Blueprint bị chặn vì workspace đã có một Key Value Free. Dùng lại Blueprint lab12 và Redis day12-redis. Sau đó app báo ValidationError: agent_api_key Field required và thoát status 3. Thêm AGENT_API_KEY trong Environment của day12-agent và deploy lại commit 3818df1. Các kiểm tra public bên trên đã xác nhận app chạy và kết nối Redis.

Không dùng LOCAL_FALLBACK.

## Kết Quả Chấm Tự Động

Chạy ngày 2026-09-28:

```bash
.venv/bin/python -m pytest tests/test_cp1.py tests/test_cp2.py tests/test_cp3.py tests/test_cp4.py tests/test_cp5.py -q
.venv/bin/python grade.py --no-bonus
```

| Phần | Kết quả |
|------|---------|
| CP1 | 13/13 pass |
| CP2 | 16/16 pass, gồm kiểm tra Docker thật |
| CP3 | 22/22 pass |
| CP4 | 19/19 pass |
| CP5 | 9/9 pass; 4 test fallback local bị skip vì dùng cloud |
| Tổng test bắt buộc | 79 pass, 4 skip, 0 fail |
| grade.py --no-bonus | 100.0/100 điểm tự động |

Điểm phản ánh chỉ đếm mức độ hoàn thành. Các câu trong exercises.md được hỗ trợ biên soạn từ kết quả thật; học viên cần đọc, kiểm chứng và giải thích được trước khi nộp. Chưa triển khai bonus CI/CD. Điểm cuối còn do giảng viên đánh giá chất lượng câu trả lời và yêu cầu nộp bài.

## Tên Repository Khi Nộp Bài

MSSV học viên xác nhận là 2A202602955. Tên repository đúng theo mẫu nộp bài là:

```text
K4-L3A-DAY12-VuThuongTin-2A202602955-CloudServicesAndDeployment
```

Repo GitHub hiện vẫn chứa L3A202602955 trong tên. Chưa đổi được tên từ workspace vì không có quyền đăng nhập GitHub phục vụ thao tác quản trị. Link trong bảng thông tin học viên ở trên là link repo đang tồn tại, không phải link dự kiến sau khi đổi tên.
