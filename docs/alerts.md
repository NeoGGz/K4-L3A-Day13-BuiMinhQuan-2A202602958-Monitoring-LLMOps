# Alert rules and runbooks

The rules in [`../config/alert_rules.yaml`](../config/alert_rules.yaml) use user-visible symptoms and SLO guardrails. Route notifications to Slack `#llmops-alerts` and the owning on-call rotation; configure that channel in the student's workspace before enabling delivery.

## Alert 1 — ElevatedUserLatency

- **Severity / duration:** warning; P95 over 3,000 ms for 5 minutes.
- **SLI:** latency-qualified successful requests, target 99.5% over 28 days.
- **User impact:** chat responses arrive too slowly and consume the latency error budget.
- **Initial checks:** (1) compare latency P50/P95/P99 and TTFT; (2) identify the time window and affected feature from logs; (3) follow a slow request's correlation ID into its trace and compare retrieval and generation spans.
- **Mitigation:** disable the affected feature or route to the local fallback if the managed prompt/backend is responsible; reduce concurrency or roll back the latest prompt/model change when the matching span identifies it. Confirm P95 recovers.
- **Owner:** platform-on-call.

## Alert 2 — UserRequestErrors

- **Severity / duration:** critical; error rate over 2% for 5 minutes.
- **SLI:** successful chat responses divided by received requests; failed requests consume the availability budget.
- **User impact:** requests fail rather than returning an answer.
- **Initial checks:** (1) inspect request volume and error rate; (2) group `request_failed` logs by `error_type` and `tool_name`; (3) correlate a failed request with its trace and inspect the first failed span.
- **Mitigation:** disable a failing integration/feature or switch to the supported fallback; if a retrieval dependency is failing, serve the safe general response or temporarily disable retrieval. Verify recovery with a new request and matching logs.
- **Owner:** api-on-call.

## Alert 3 — DegradedAnswerQuality

- **Severity / duration:** warning; retrieval success below 90% or quality proxy below 0.75 for 10 minutes.
- **SLI/guardrail:** retrieval success and the response quality proxy; these are early indicators of degraded answers rather than the primary availability SLO.
- **User impact:** answers may be irrelevant, unsupported, or incomplete even when requests return successfully.
- **Initial checks:** (1) compare retrieval success and quality by feature; (2) inspect sanitized log previews for affected requests; (3) inspect retrieval results and prompt version metadata in representative traces.
- **Mitigation:** roll back the most recently promoted prompt label, restore the last known-good retrieval configuration, and rerun a small known-query set. Keep the change only after both retrieval success and quality recover.
- **Owner:** llm-on-call.

## Shared response notes

Use the investigation order **Metrics → Logs → Traces**. Record the alert time window, affected feature, sanitized correlation ID, trace ID, suspected span, mitigation, and recovery metric in the incident report. Do not paste raw prompts, user messages, secrets, or PII into Slack.
