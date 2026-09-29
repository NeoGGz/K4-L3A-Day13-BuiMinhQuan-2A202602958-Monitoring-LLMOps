"""Small runtime dashboard backed by the lab's JSONL log source."""

from __future__ import annotations

import html
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

import yaml

from .metrics import percentile


REPO_ROOT = Path(__file__).resolve().parents[1]


def _recent_records(path: Path, now: datetime, minutes: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    start = now - timedelta(minutes=minutes)
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
            timestamp = datetime.fromisoformat(record["ts"].replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            if start <= timestamp.astimezone(timezone.utc) <= now:
                records.append(record)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            continue
    return records


def _bars(
    values: list[float], *, color: str = "#5b8def", threshold: float | None = None
) -> str:
    peak = max(max(values, default=0), threshold or 0) or 1
    items = "".join(
        f'<span class="bar" title="{value:.2f}" '
        f'style="height:{max(2, value / peak * 100):.1f}%;background:{color}"></span>'
        for value in values
    )
    threshold_line = (
        f'<i class="threshold-line" style="bottom:{min(98, threshold / peak * 100):.1f}%"></i>'
        if threshold is not None else ""
    )
    return (
        f'<div class="bars" data-scale="{peak}" data-threshold="{threshold if threshold is not None else ""}" '
        f'role="img" aria-label="Values over the last 60 minutes">{items}{threshold_line}</div>'
    )


def _card(title: str, value: str, details: str, chart: str, threshold: str) -> str:
    return (
        '<section class="card">'
        f'<h2>{html.escape(title)}</h2><div class="value">{value}</div>'
        f'<div class="details">{details}</div>{chart}'
        f'<div class="threshold">Threshold: {html.escape(threshold)}</div>'
        '</section>'
    )


def render_dashboard(
    log_path: Path | None = None,
    config_path: Path | None = None,
    now: datetime | None = None,
) -> str:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    config = yaml.safe_load(
        (config_path or REPO_ROOT / "config" / "dashboard.yaml").read_text(encoding="utf-8")
    )["dashboard"]
    minutes = config["time_range_minutes"]
    panels = {panel["id"]: panel for panel in config["panels"]}
    records = _recent_records(log_path or REPO_ROOT / "data" / "logs.jsonl", now, minutes)
    start_minute = now.replace(second=0, microsecond=0) - timedelta(minutes=minutes - 1)
    keys = [(start_minute + timedelta(minutes=i)).isoformat() for i in range(minutes)]

    def buckets(event: str, field: str | None = None) -> list[list[float]]:
        grouped: dict[str, list[float]] = defaultdict(list)
        for record in records:
            if record.get("event") != event:
                continue
            timestamp = datetime.fromisoformat(record["ts"].replace("Z", "+00:00"))
            key = timestamp.astimezone(timezone.utc).replace(second=0, microsecond=0).isoformat()
            if field is None:
                grouped[key].append(1.0)
            elif isinstance(record.get(field), (int, float)):
                grouped[key].append(float(record[field]))
        return [grouped[key] for key in keys]

    def threshold(panel_id: str) -> str:
        panel = panels[panel_id]
        item = panel["threshold"]
        return f'{item["aggregation"]} {item["operator"]} {item["value"]} {panel["unit"]}'

    responses = [record for record in records if record.get("event") == "response_sent"]
    requests = [record for record in records if record.get("event") == "request_received"]
    failures = [record for record in records if record.get("event") == "request_failed"]
    latencies = [int(record["latency_ms"]) for record in responses if isinstance(record.get("latency_ms"), (int, float))]
    ttfts = [int(record["ttft_ms"]) for record in responses if isinstance(record.get("ttft_ms"), (int, float))]
    latency_by_minute = buckets("response_sent", "latency_ms")
    latency_chart = _bars(
        [percentile([int(v) for v in values], 95) for values in latency_by_minute],
        threshold=3000,
    )
    latency = _card(
        panels["latency"]["title"],
        f'{percentile(latencies, 95):.0f} ms P95',
        f'P50 {percentile(latencies, 50):.0f} ms · P99 {percentile(latencies, 99):.0f} ms · TTFT P95 {percentile(ttfts, 95):.0f} ms',
        latency_chart,
        threshold("latency"),
    )

    traffic_per_minute = [len(values) for values in buckets("request_received")]
    traffic = _card(
        panels["traffic"]["title"],
        f'{len(requests)} requests',
        f'{len(requests) / minutes:.2f} requests/minute across the window',
        _bars(traffic_per_minute, threshold=1),
        threshold("traffic"),
    )

    error_rate = len(failures) / len(requests) * 100 if requests else 0.0
    tool_events = [record for record in records if isinstance(record.get("tool_success"), bool)]
    retrieval_success = (
        sum(record["tool_success"] for record in tool_events) / len(tool_events) * 100
        if tool_events else 0.0
    )
    error_types = Counter(str(record.get("error_type") or "unknown") for record in failures)
    breakdown = ", ".join(f"{html.escape(name)}: {count}" for name, count in error_types.items()) or "none"
    failures_by_minute = [len(values) for values in buckets("request_failed")]
    error_rates_by_minute = [
        failed / received * 100 if received else 0
        for failed, received in zip(failures_by_minute, traffic_per_minute)
    ]
    errors = _card(
        panels["errors"]["title"],
        f'{error_rate:.2f}% errors',
        f'Retrieval success {retrieval_success:.1f}% · Errors by type: {breakdown}',
        _bars(error_rates_by_minute, color="#dc5962", threshold=2),
        threshold("errors"),
    )

    costs = [float(record.get("cost_usd") or 0) for record in responses]
    cost_per_minute = [sum(values) for values in buckets("response_sent", "cost_usd")]
    cost = _card(
        panels["cost"]["title"],
        f'${sum(costs):.4f}',
        f'Peak ${max(cost_per_minute, default=0):.4f} per minute',
        _bars(cost_per_minute, color="#c29142"),
        threshold("cost"),
    )

    tokens_in = sum(int(record.get("tokens_in") or 0) for record in responses)
    tokens_out = sum(int(record.get("tokens_out") or 0) for record in responses)
    in_by_minute = buckets("response_sent", "tokens_in")
    out_by_minute = buckets("response_sent", "tokens_out")
    token_series = [sum(a) + sum(b) for a, b in zip(in_by_minute, out_by_minute)]
    tokens = _card(
        panels["tokens"]["title"],
        f'{tokens_in + tokens_out:,} tokens',
        f'Input {tokens_in:,} · Output {tokens_out:,}',
        _bars(token_series, color="#9276c5"),
        threshold("tokens"),
    )

    scores = [float(record["quality_score"]) for record in responses if isinstance(record.get("quality_score"), (int, float))]
    quality_by_minute = buckets("response_sent", "quality_score")
    quality = _card(
        panels["quality"]["title"],
        f'{mean(scores):.2f} mean' if scores else 'No scores',
        f'{len(scores)} scored responses',
        _bars(
            [mean(values) if values else 0 for values in quality_by_minute],
            color="#45a58b",
            threshold=0.75,
        ),
        threshold("quality"),
    )

    note = "" if records else '<p class="empty">No log events in the last 60 minutes. Run the load test to populate this dashboard.</p>'
    cards = latency + traffic + errors + cost + tokens + quality
    export_script = (REPO_ROOT / "app" / "dashboard_export.js").read_text(encoding="utf-8")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="{config['refresh_seconds']}">
<title>{html.escape(config['title'])}</title>
<style>
body {{ margin:0; padding:32px; background:#f4f6fa; color:#172538; font-family:system-ui, sans-serif; }}
main {{ max-width:1200px; margin:auto; }}
h1 {{ margin:0 0 6px; font-size:28px; }}
.meta {{ color:#566377; margin:0 0 28px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(330px,1fr)); gap:18px; }}
.card {{ background:white; border:1px solid #dfe5ee; border-radius:14px; padding:22px; box-shadow:0 3px 12px #1725380a; }}
h2 {{ font-size:17px; margin:0 0 18px; }}
.value {{ font-size:30px; font-weight:700; margin-bottom:8px; }}
.details {{ color:#42516a; font-size:14px; min-height:40px; }}
.bars {{ position:relative; height:86px; display:flex; align-items:end; gap:2px; margin:18px 0; border-bottom:1px solid #dfe5ee; }}
.bar {{ flex:1; min-width:2px; border-radius:2px 2px 0 0; }}
.threshold-line {{ position:absolute; left:0; right:0; border-top:2px dashed #e05b57; pointer-events:none; }}
.threshold {{ font-size:13px; color:#59687a; border-top:1px solid #eef1f5; padding-top:12px; }}
.empty {{ padding:12px 16px; background:#fff3d8; border-radius:8px; }}
.download {{ float:right; border:0; border-radius:8px; padding:10px 16px; color:white; background:#285bad; font:600 14px system-ui; cursor:pointer; }}
</style></head><body><main>
<button id="download-dashboard" class="download" type="button">Download PNG</button>
<h1>{html.escape(config['title'])}</h1>
<p class="meta">Source: data/logs.jsonl · Time range: last {minutes} minutes · Refresh: {config['refresh_seconds']} seconds · Updated: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
{note}<div class="grid">{cards}</div>
</main><script>{export_script}</script></body></html>"""
