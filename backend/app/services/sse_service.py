"""SSE 编码工具，确保换行等字符安全地留在单个事件中。"""
from __future__ import annotations

import json
from typing import Any


AGENT_EVENT_TYPES = {"meta", "tool_start", "tool_end", "tool_error"}


def encode_sse_event(event_type: str, **payload: Any) -> str:
    data = {"type": event_type, **payload}
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def encode_agent_stream_item(item: str) -> str:
    """保留 Agent 结构化事件，其余内容统一包装为文本事件。"""
    if item.startswith("{"):
        try:
            event = json.loads(item)
            event_type = event.get("type")
            if event_type in AGENT_EVENT_TYPES:
                return encode_sse_event(
                    event_type,
                    **{key: value for key, value in event.items() if key != "type"},
                )
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
    return encode_sse_event("text", content=item)
