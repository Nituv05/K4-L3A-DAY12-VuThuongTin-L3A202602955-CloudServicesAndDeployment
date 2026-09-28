# Phiếu Phản Ánh — K4 Level 3A, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Nội dung được hoàn thiện với sự hỗ trợ của trợ lý, dựa trên code, log và kết quả
> chạy thật ngày 2026-09-28. Học viên cần đọc và giải thích được nội dung trước khi nộp.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Vũ Thường Tín  Mã học viên: L32A202602955

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

Trong lần deploy Render, app thiếu AGENT_API_KEY và dừng với lỗi “agent_api_key — Field required”. Điều này giúp phát hiện cấu hình thiếu ngay trong log trước khi service nhận request. Nếu tự dùng khóa mặc định changeme, app có thể vẫn chạy nhưng bất kỳ ai biết khóa mẫu đều gọi được /ask. Cách xử lý thực tế là thêm AGENT_API_KEY trong Environment của day12-agent rồi deploy lại.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

Dòng log thật từ agent-2 của stack local:

```json
{"user_id":"submission-evidence-20260928","tokens_in":88,"tokens_out":50,"cost_usd":4.32e-05,"event":"ask_completed","level":"info","timestamp":"2026-09-28T13:29:46.582047+00:00"}
```

Có thể lọc event ask_completed theo user_id và thời gian để kiểm tra một người dùng đã được xử lý những lượt nào. Có thể cộng cost_usd hoặc thống kê tokens_in/tokens_out theo ngày để theo dõi chi phí. Chuỗi print không có các trường này nên khó lọc và tổng hợp tự động.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f Dockerfile.single -t agent:single .
docker build -t agent:multi .
docker images | grep agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (baseline dựng lại) | 63.967774 MB |
| Multi-stage | 63.968377 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

Đã build thật ngày 2026-09-28 bằng Dockerfile.single và Dockerfile. Bản single-stage được dựng lại để so sánh cùng base python:3.11-slim và cùng requirements.txt; đây không phải số đo đã lưu từ bản đầu buổi lab.

```bash
docker build -f Dockerfile.single -t agent:single .
docker build -t agent:multi .
docker image inspect agent:single agent:multi --format '{{index .RepoTags 0}} {{.Size}}'
```

Output: agent:single 63967774; agent:multi 63968377 (byte theo trường Size của docker image inspect). Bảng dùng MB = 1.000.000 byte. Hai bản gần như bằng nhau; multi-stage lớn hơn 603 byte theo phép đo này. Cả hai đều dùng slim, không cài compiler và đều bỏ pip cache, nên không có bộ build tool lớn để loại bỏ. Không thể kết luận multi-stage luôn làm image nhỏ hơn; lợi ích rõ khi builder có compiler, header hoặc artifact trung gian mà runtime không cần. Docker Desktop có thể hiển thị dung lượng khác theo disk usage; không trộn hai cách đo.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

Đã kiểm tra bằng cách thêm một ký tự # ở cuối bản sao app/main.py trong context build tạm, rồi build image day12-agent:cache-check. Mã nguồn chính và container đang chạy không bị thay đổi. Build thành công và cho kết quả:

```text
COPY requirements.txt .                                  CACHED
RUN pip install --no-cache-dir ... --prefix=/install      CACHED
COPY --from=builder /install /usr/local                   CACHED
RUN useradd --create-home --uid 10001 appuser              CACHED
COPY app ./app                                           DONE
COPY utils ./utils                                       DONE
```

COPY app mất cache vì nội dung app/main.py thay đổi. COPY utils nằm sau layer đó nên cũng chạy lại dù utils không đổi. Các layer dependency đứng trước source vẫn dùng cache. Nếu chuyển COPY toàn bộ source lên trước RUN pip install, mỗi lần sửa source sẽ làm pip install chạy lại, khiến build chậm hơn.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

Ví dụ lỗ hổng cho phép chạy lệnh Python/shell khiến kẻ tấn công có quyền của process trong container. Nếu process chạy root, họ có thể sửa nhiều file hơn trong container và tận dụng cấu hình nguy hiểm như mount thư mục host có quyền ghi, privileged hoặc lỗ hổng kernel để gây ảnh hưởng tới host. Root trong container không tự động là root trên host. USER appuser giới hạn quyền process ngay từ đầu, giảm khả năng ghi vào đường dẫn đặc quyền; nó không thay thế việc tránh privileged, Docker socket và các mount nhạy cảm.

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

Fixed window có thể cho qua 20 request trong hai giây: gửi 10 request lúc 12:00:59 và 10 request lúc 12:01:00 vì bộ đếm đã reset. Sliding window xét 60 giây gần nhất nên 10 request trước ranh giới phút vẫn được tính và nhóm request tiếp theo bị chặn.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

Rate limit kiểm soát số request trong 60 giây, còn cost guard kiểm soát chi phí tích lũy trong tháng theo người dùng. Một người chỉ gọi 1 request/phút nhưng đã dùng hết ngân sách tháng sẽ qua rate limit và bị cost guard trả 402. Ngược lại, một người còn nhiều ngân sách nhưng gửi request thứ 11 trong 60 giây sẽ bị rate limit trả 429. Cả hai được kiểm tra trước ask_llm để không phát sinh tiền rồi mới chặn.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

Khi Redis mất kết nối, /ready trả 503 để báo instance chưa phục vụ request cần Redis; /health vẫn trả 200 vì process còn sống. Nếu dùng chung endpoint kiểm tra Redis, cả ba agent có thể bị đánh dấu không khỏe cùng lúc. Với orchestrator dùng endpoint đó làm liveness và lỗi vượt ngưỡng, nó có thể restart agent dù nguyên nhân ở Redis; restart không khôi phục Redis và dễ lặp lại. Khi Redis hồi phục, các agent phải kết nối lại rồi mới sẵn sàng. Docker Compose healthcheck chỉ đánh dấu unhealthy, không tự restart container chỉ vì healthcheck lỗi; trong 30 giây có restart hay không còn phụ thuộc orchestrator và ngưỡng probe.

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

Stack local có ba container agent healthy. Năm request tuần tự cùng X-User-Id submission-evidence-20260928 trả history_length 0, 2, 4, 6, 8 và đều HTTP 200. Mỗi lượt thêm hai message user/assistant; response trả độ dài history trước lượt hiện tại. Log xác nhận hai lượt đầu ở agent-3, lượt thứ ba ở agent-2 và hai lượt cuối ở agent-1. Lịch sử vẫn tăng đều khi chuyển container. Redis giúp các instance đọc chung history. Nếu mỗi instance dùng dict Python riêng, khi request chuyển container có thể lại thấy 0 hoặc một giá trị thấp hơn; dãy không đảm bảo tăng đều. Thử nghiệm này là các request tuần tự, không chứng minh thứ tự history khi nhiều request cùng user chạy đồng thời.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

Render build Docker thành công nhưng app thoát status 3. Log ghi “pydantic_core.ValidationError: 1 validation error for Settings”, trường agent_api_key “Field required”; traceback đi qua lifespan → get_settings → Settings. Nguyên nhân là Environment của day12-agent chưa có AGENT_API_KEY. Cấu hình sync: false không tự thêm khóa khi cập nhật Blueprint cũ. Thêm biến vào dashboard và deploy lại commit 3818df1 đã sửa lỗi. Sau đó kiểm tra public URL: /health 200, /ready 200, /ask thiếu khóa 401, /ask có khóa 200. Trước đó tạo Blueprint trùng còn gặp giới hạn một Key Value Free, được xử lý bằng dùng lại Blueprint lab12 và Redis day12-redis.
