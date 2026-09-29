# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Số liệu local bên dưới được đo từ workload ngày 29/09/2026. Evidence Langfuse và challenge chính thức chỉ được điền sau khi dùng project/file riêng của học viên.

## 1. Thông tin học viên

- **Họ và tên:** Bùi Minh Quân
- **MSSV:** 2A202602958
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/NeoGGz/K4-L3A-Day13-BuiMinhQuan-2A202602958-Monitoring-LLMOps
- **Tên repo cần rà soát:** URL hiện có `K4-L3A-Day13-...`, trong khi `docs/SUBMISSION.md` yêu cầu mẫu `K4-L3-DAY13-HoVaTen-MSSV-Monitoring-LLMOps`; cần đổi tên hoặc xác nhận quy ước với Lab Coach trước khi nộp.
- **Commit SHA cuối:** [điền sau commit nộp]
- **Challenge ID:** [chỉ điền sau khi Lab Coach release]
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602958` ([project](https://cloud.langfuse.com/project/cmumrr8r001evad0chsjpadw3))

## 2. Evidence index

Chỉ thêm đường dẫn khi evidence thật đã được lưu trong `submission/evidence/`. Không đưa ảnh chứa API key, secret hoặc PII.

| Evidence | Trạng thái / đường dẫn |
|---|---|
| Pytest cuối | [`evidence/01-pytest.txt`](evidence/01-pytest.txt) |
| Log validator | [`evidence/02-log-validator.txt`](evidence/02-log-validator.txt) |
| Dashboard validator | [`evidence/03-dashboard-validator.txt`](evidence/03-dashboard-validator.txt) |
| Structured log và correlation ID | [`evidence/04-structured-log.json`](evidence/04-structured-log.json) |
| PII redaction | [`evidence/05-pii-redaction.json`](evidence/05-pii-redaction.json) |
| Trace list / waterfall / metadata | Cần key và project Langfuse cá nhân |
| Prompt versions / rollback | [Prompt `day13-chat`](https://cloud.langfuse.com/project/cmumrr8r001evad0chsjpadw3/prompts/day13-chat): đã tạo v1/v2 và các label; còn trace so sánh và rollback |
| Dashboard runtime | [`evidence/11-dashboard-overview.png`](evidence/11-dashboard-overview.png) |
| Practice incident metric / log | [`evidence/12-practice-incident-metrics.json`](evidence/12-practice-incident-metrics.json), [`evidence/13-practice-incident-log.json`](evidence/13-practice-incident-log.json) |
| Challenge chính thức: metric / log / trace | Chỉ điền sau khi có file riêng của lớp và project Langfuse |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | Không đo trước khi sửa source | 100/100 | 49 log records, 24 correlation IDs |
| `validate_dashboard.py` | Không đo trước khi sửa source | 6/6 panel | YAML contract hợp lệ; runtime có ảnh |
| `pytest` | Lần đầu lỗi quyền thư mục tạm Windows | 24 passed | Chạy lại với `--basetemp` trong workspace |
| Số traces hợp lệ | 0 | 0 | Project và prompt đã có; `.env` chưa có key |
| Số PII leak | — | 0 | Log validator trên toàn bộ log local |
| Latency P95 / TTFT P95 | 151 / 50 ms | 2652 / 50 ms sau practice `rag_slow` | `/metrics` cộng dồn 20 request; client latency cao hơn do concurrency |
| Retrieval success rate | 100% | 100% | Practice `rag_slow` chỉ tăng latency |

## 4. Logging và PII

- Correlation ID được nhận khi header `x-request-id` khớp `req-<8 hex>`; nếu không, server sinh ID mới. Response trả `x-request-id` và `x-response-time-ms`.
- Structured log được enrich với `user_id_hash`, `session_id`, `feature`, `model`, `env` và correlation ID. User ID được SHA-256 hash trước khi bind.
- Processor scrub chạy trước file writer và JSON renderer, duyệt các giá trị string lồng trong object/list. Pattern gồm email, số điện thoại Việt Nam, CCCD, thẻ thanh toán, passport dạng phổ biến và giá trị có nhãn địa chỉ.
- Log ghi nội dung preview đã sanitize; không ghi raw prompt/output vào Langfuse observations.
- **Kết quả kiểm chứng:** log validator đạt 100/100, không phát hiện PII raw; các log mẫu cho email, điện thoại, CCCD và thẻ nằm tại [`evidence/05-pii-redaction.json`](evidence/05-pii-redaction.json). Một request với header `req-abcdef12` trả cùng ID và `x-response-time-ms`.

## 5. Tracing và prompt versioning

- Cây trace dự kiến: root `lab-agent-run` → child `retrieval` → child `llm-generation`.
- Root metadata gồm correlation ID, feature, model và prompt name/label/version/source. Retrieval span lưu preview đã scrub và số document; generation lưu model, token usage, cost estimate và TTFT. Raw prompt/output không được gửi làm observation input/output.
- **Trace IDs:** [thêm ít nhất 10 IDs từ project cá nhân].
- **Prompt name / version / label baseline / candidate:** `day13-chat` v1 có `baseline`, `production`; v2 có `candidate` (`latest` tự động). Cả hai giữ `feature`, `docs`, `message`. [Xem trên Langfuse](https://cloud.langfuse.com/project/cmumrr8r001evad0chsjpadw3/prompts/day13-chat).
- **Trace ID baseline / candidate:** [điền].
- **Promote và rollback production:** [ghi lại lần chuyển label và hai trace xác nhận version].

## 6. Dashboard, SLO và alerts

- Dashboard contract trong `config/dashboard.yaml` định nghĩa sáu panel: latency (P50/P95/P99, TTFT), traffic, errors/retrieval success, cost, tokens và quality proxy.
- SLO được đặt là 99.5% request thành công trong 3 giây trên cửa sổ 28 ngày; error budget là 0.5% tổng eligible requests. Ví dụ 100,000 request tương ứng tối đa 500 request ngoài SLI. Cần hiệu chỉnh theo baseline đo thực tế trước khi dùng production.
- Ba alert symptom-based (Slack): P95 > 3,000 ms trong 5 phút; error rate > 2% trong 5 phút; retrieval success < 90% hoặc quality proxy < 0.75 trong 10 phút. Runbook: [`../docs/alerts.md`](../docs/alerts.md).
- **Dashboard runtime/evidence:** [`evidence/11-dashboard-overview.png`](evidence/11-dashboard-overview.png) được xuất từ `/dashboard` sau 20 request. Trang dùng `data/logs.jsonl`, range 60 phút, refresh 30 giây và hiển thị threshold từng panel. Validator chỉ kiểm tra contract YAML.

## 7. Điều tra challenge

Chưa có file challenge chính thức trong repository. Không tự tạo hoặc suy đoán challenge K4-L3A.

- **Challenge ID / khoảng thời gian:** [điền từ file Lab Coach]
- **Triệu chứng metrics:** [điền]
- **Log line / correlation ID:** [điền, không đưa PII]
- **Trace ID / span gây ảnh hưởng:** [điền từ project cá nhân]
- **Root cause / fix action / preventive measure:** [điền theo bằng chứng metrics → log → trace]

### Practice local (không thay thế challenge chính thức)

- Bật `rag_slow`, chạy cùng 10 sample queries ở concurrency 5 rồi tắt incident.
- Baseline P95 = 151 ms; sau practice P95 cộng dồn = 2652 ms, trong khi TTFT P95 = 50 ms. Xem [`evidence/15-baseline-metrics.json`](evidence/15-baseline-metrics.json) và [`evidence/12-practice-incident-metrics.json`](evidence/12-practice-incident-metrics.json).
- Log `req-e51404da` có `request_received` lúc 14:11:06 UTC và `response_sent` lúc 14:11:08 UTC với `latency_ms=2652`, `ttft_ms=50`. Xem [`evidence/13-practice-incident-log.json`](evidence/13-practice-incident-log.json).
- Với scenario đã bật, độ trễ tăng ở bước retrieval; cần trace Langfuse có cùng correlation ID để xác nhận bằng waterfall. Chưa có trace nên đây chỉ là chẩn đoán practice từ metric, log và cấu hình incident.
- Mitigation đã thực hiện: tắt `rag_slow`; `/health` xác nhận mọi incident đều `false`.

## 8. Giải thích và tự đánh giá

- Quyết định kỹ thuật chính là scrub dữ liệu trước cả hai sink logging và tránh capture raw input/output trong trace; điều này giảm nguy cơ lộ PII ở nhiều lớp quan sát.
- Correlation ID nối request log với trace metadata, còn child spans tách thời gian retrieval và generation để khoanh vùng nguyên nhân.
- Prompt label là con trỏ triển khai; rollback kiểm chứng bằng trace mới ghi nhận lại version sau khi label production được chuyển về bản trước.
- **Blocker / cách xử lý:** Python 3.14 trên Windows thiếu wheel cho `pydantic-core` bản đã khóa và máy thiếu MSVC linker; đã cài Python 3.13 trong workspace rồi tạo lại `.venv`. Pytest đầu tiên bị lỗi quyền ở thư mục Temp; chạy lại với `--basetemp` trong workspace và đạt 24/24.
- **Giới hạn hiện tại:** project Langfuse và prompt versions đã có, nhưng chưa có key trong `.env` nên chưa có trace hay rollback đã kiểm chứng; chưa có challenge riêng của lớp. Code và kết quả local chưa nằm trên commit nộp cuối.

## 9. Checklist trước khi nộp

- [ ] Điền commit SHA của commit nộp cuối.
- [ ] Rà tên repository theo quy ước nộp bài.
- [x] Chạy workload local, pytest và hai validators; cập nhật số liệu thật.
- [x] Dựng dashboard runtime sáu panel và lưu ảnh dữ liệu thật.
- [ ] Có ít nhất 10 traces cá nhân, prompt v1/v2 và rollback.
- [ ] Khi Lab Coach release challenge, nối metric → log → trace cho cùng request.
- [x] Lưu evidence local bằng đường dẫn tương đối trong `submission/evidence/`.
- [ ] Rà soát secret, raw PII và file challenge trước khi push.
