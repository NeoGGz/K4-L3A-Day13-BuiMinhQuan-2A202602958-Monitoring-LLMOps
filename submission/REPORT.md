# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Số liệu local được đo ngày 29/09/2026; trace Langfuse cá nhân được đo ngày 30/09/2026. Challenge chính thức cần file riêng từ Lab Coach.

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
| Trace list / waterfall / metadata | [`evidence/14-langfuse-trace-index.json`](evidence/14-langfuse-trace-index.json); [mở tracing](https://cloud.langfuse.com/project/cmumrr8r001evad0chsjpadw3/traces); practice trace `462ca36dcf6c7b71786d89710a841f2b` |
| Prompt versions / rollback | [Prompt `day13-chat`](https://cloud.langfuse.com/project/cmumrr8r001evad0chsjpadw3/prompts/day13-chat); baseline/candidate và promote/rollback trong trace index |
| Dashboard runtime | [`evidence/11-dashboard-overview.png`](evidence/11-dashboard-overview.png) |
| Practice incident metric / log | [`evidence/12-practice-incident-metrics.json`](evidence/12-practice-incident-metrics.json), [`evidence/13-practice-incident-log.json`](evidence/13-practice-incident-log.json) |
| Challenge chính thức: metric / log / trace | Chỉ điền sau khi có file riêng của lớp và project Langfuse |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | Không đo trước khi sửa source | 100/100 | 167 log records, 80 correlation IDs; 0 PII leak |
| `validate_dashboard.py` | Không đo trước khi sửa source | 6/6 panel | YAML contract hợp lệ; runtime có ảnh |
| `pytest` | Lần đầu lỗi quyền thư mục tạm Windows | 24 passed | Chạy lại với `--basetemp` và quyền ghi phù hợp trong workspace |
| Số traces hợp lệ | 0 | 32 | 10 baseline v1, 10 candidate v2, 10 practice `rag_slow`, 1 promote v2, 1 rollback v1; mỗi trace có 3 observations |
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

- Cây trace đã xác nhận: root `lab-agent-run` → child `retrieval` → child `llm-generation`. Mỗi trace có một observation mỗi loại, tổng 96 observations cho 32 request trong trace index.
- Root metadata gồm correlation ID, feature, model và prompt name/label/version/source. Retrieval span lưu preview đã scrub và số document; generation lưu model, token usage, cost estimate và TTFT. Raw prompt/output không được gửi làm observation input/output.
- **Trace IDs baseline (10):** `11b32179fb89b75d148b7c768bfbfc1a`, `72d89607cfc9046cea73a8f2fb2bcb1c`, `0ec995962e700d470637ea3825980bf8`, `3e98ca044b2781c94d5de9ab748a5177`, `f7653d796d5e987c63992abd1849de2b`, `ae9244715a601e92733fb141c5f96265`, `4b10b7a895fbfffd8256f7fc27a20017`, `d040c0b3b9a5ddaa528239f2ef4f25a5`, `877881e79816d3d5f9b8d884cbca35f3`, `83bc1b8b6329dd2ce03ad2e971779683`.
- **Trace IDs candidate (10):** `c0337bd9e315445e18ff5de04ff62666`, `fc44f7fc242a32fc9a7bb9076befb65c`, `c7609698038322203e0045d3bd7ef17f`, `fd5ac34dc3efc3b0e8985495e813b430`, `a99717d44ffccc9ba2b02f6af9cd8753`, `6921e6b54ddc574cedf6394d4804ae74`, `a8cbe364ef558aa8f1c9b0d9f748b00c`, `fa8f2ffe507d978e543c5f2053f6d765`, `7a0f8e5b0148be8af21cabf7e63883bd`, `3a3a32889829666778299abac4b6985e`.
- **Prompt name / version / label baseline / candidate:** `day13-chat` v1 có `baseline`, `production`; v2 có `candidate` (`latest` tự động). Cả hai giữ `feature`, `docs`, `message`. [Xem trên Langfuse](https://cloud.langfuse.com/project/cmumrr8r001evad0chsjpadw3/prompts/day13-chat).
- **Trace ID baseline / candidate:** `11b32179fb89b75d148b7c768bfbfc1a` (`req-d2dbfb7f`, label `baseline`, v1) / `c0337bd9e315445e18ff5de04ff62666` (`req-845a3e29`, label `candidate`, v2). Cùng bộ 10 sample queries, mỗi lượt 10/10 HTTP 200; workload lưu tại [`evidence/07-prompt-baseline-workload.txt`](evidence/07-prompt-baseline-workload.txt) và [`evidence/08-prompt-candidate-workload.txt`](evidence/08-prompt-candidate-workload.txt).
- **Độ trễ so sánh:** trong mỗi nhóm 10 trace, 9 request sau khi prompt đã được cache khoảng 151–152 ms; request đầu tải prompt từ Langfuse khoảng 984–985 ms. Đây là fake LLM nên số liệu chỉ minh họa overhead của prompt fetch và pipeline lab.
- **Promote và rollback production:** chuyển `production` sang v2; trace `fac8e37cb0d9ceb3fa2599f7007c3709` (`req-4123db7c`) xác nhận `prompt_source=langfuse`, `prompt_label=production`, `prompt_version=2`. Chuyển `production` về v1; trace `5ad31ae1f7c4247ac965d427b5084655` (`req-057f93f8`) xác nhận version 1. Trạng thái cuối: v1 có `baseline`, `production`; v2 có `candidate`, `latest`. Request evidence: [`evidence/09-production-v2-request.json`](evidence/09-production-v2-request.json), [`evidence/10-rollback-v1-request.json`](evidence/10-rollback-v1-request.json).

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
- Ở lượt practice local đầu, độ trễ tăng khi bật `rag_slow`; lúc đó chưa có trace nên chỉ có metric và log. Lượt practice có Langfuse ngày 30/09/2026 bên dưới đã xác nhận bằng waterfall.
- Mitigation đã thực hiện: tắt `rag_slow`; `/health` xác nhận mọi incident đều `false`.

### Practice có trace Langfuse (30/09/2026)

- Bật lại `rag_slow`, chạy 10 sample queries với concurrency 5 rồi tắt incident. Trạng thái cuối của `/health`: `tracing_enabled=true`, cả ba incident `false`.
- Metric trước workload: traffic 1, latency P95 995 ms, TTFT P95 50 ms. Sau workload: traffic 11, latency P95 2652 ms, TTFT P95 50 ms, retrieval success 100%. Đây là metric cộng dồn từ lần restart API gần nhất, không phải cửa sổ chỉ gồm request incident. Evidence: [`evidence/16-live-practice-baseline-metrics.json`](evidence/16-live-practice-baseline-metrics.json), [`evidence/18-live-practice-incident-metrics.json`](evidence/18-live-practice-incident-metrics.json).
- Log `req-06054992` ghi `response_sent` latency 2651 ms và TTFT 50 ms tại [`evidence/19-live-practice-log.json`](evidence/19-live-practice-log.json). Trace cùng correlation ID `462ca36dcf6c7b71786d89710a841f2b` cho thấy root 2652 ms, retrieval 2500 ms và generation 151 ms. Như vậy bước retrieval chiếm phần lớn độ trễ; không phải thời gian sinh token đầu. Trace nằm trong [`evidence/14-langfuse-trace-index.json`](evidence/14-langfuse-trace-index.json), workload ở [`evidence/17-live-practice-workload.txt`](evidence/17-live-practice-workload.txt).
- Đây là practice có đủ metric → log → trace để minh họa cách điều tra. Root cause của challenge chính thức vẫn chờ file K4-L3A từ Lab Coach.

## 8. Giải thích và tự đánh giá

- Quyết định kỹ thuật chính là scrub dữ liệu trước cả hai sink logging và tránh capture raw input/output trong trace; điều này giảm nguy cơ lộ PII ở nhiều lớp quan sát.
- Correlation ID nối request log với trace metadata, còn child spans tách thời gian retrieval và generation để khoanh vùng nguyên nhân.
- Prompt label là con trỏ triển khai; rollback kiểm chứng bằng trace mới ghi nhận lại version sau khi label production được chuyển về bản trước.
- **Blocker / cách xử lý:** Python 3.14 trên Windows thiếu wheel cho `pydantic-core` bản đã khóa và máy thiếu MSVC linker; đã cài Python 3.13 trong workspace rồi tạo lại `.venv`. Pytest đầu tiên bị lỗi quyền ở thư mục Temp; chạy lại với `--basetemp` trong workspace và đạt 24/24.
- **Giới hạn hiện tại:** project Langfuse, 32 trace hợp lệ và rollback đã kiểm chứng; chưa có challenge riêng của lớp nên chưa thể kết luận root cause chính thức. Evidence ảnh từ giao diện Langfuse vẫn cần bổ sung; trace index JSON và link project cho phép kiểm tra trực tiếp.

## 9. Checklist trước khi nộp

- [ ] Điền commit SHA của commit nộp cuối.
- [ ] Rà tên repository theo quy ước nộp bài.
- [x] Chạy workload local, pytest và hai validators; cập nhật số liệu thật.
- [x] Dựng dashboard runtime sáu panel và lưu ảnh dữ liệu thật.
- [x] Có ít nhất 10 traces cá nhân, prompt v1/v2 và rollback.
- [ ] Khi Lab Coach release challenge, nối metric → log → trace cho cùng request.
- [x] Lưu evidence local bằng đường dẫn tương đối trong `submission/evidence/`.
- [ ] Rà soát secret, raw PII và file challenge trước khi push.
