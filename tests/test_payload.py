from __future__ import annotations

from datetime import datetime

from nonebot_plugin_yijing.core.hexagram import resolve_by_lines
from nonebot_plugin_yijing.models import CastRecord
from nonebot_plugin_yijing.services.payload import (
    build_hexagram_query_payload,
    build_history_payload,
    build_record_card_payload,
    build_record_payload_from_dict,
)


def _record() -> CastRecord:
    return CastRecord(
        id="YJ-TEST0001",
        adapter="onebot.v11",
        bot_id="10000",
        group_id="20000",
        user_id_hash="user-hash",
        question_text="此行去山西实习一程怎么样",
        question_norm="此行去山西实习一程怎么样",
        question_hash="question-hash",
        method="coin",
        coins_json='[["正", "反", "正"]]',
        line_values_json="[7, 8, 9, 6, 7, 8]",
        moving_positions_json="[3, 4]",
        primary_seq=63,
        changed_seq=64,
        preprocess_json='{"allowed": true, "warnings": [], "llm_used": false}',
        interpretation_json='{"summary": "测试摘要", "advice": ["测试建议"]}',
        created_at=datetime(2026, 7, 8, 12, 0, 0),
    )


def test_record_card_payload_contains_template_sections() -> None:
    resolved = resolve_by_lines([7, 8, 9, 6, 7, 8])

    payload = build_record_card_payload(
        record_id="YJ-TEST0001",
        question="此行去山西实习一程怎么样",
        method="coin",
        coins=[["正", "反", "正"]],
        resolved=resolved,
        preprocess={"allowed": True, "warnings": [], "llm_used": False},
        interpretation={"summary": "测试摘要", "advice": ["测试建议"]},
        cast_trace={"kind": "coin"},
        created_at="2026-07-08 12:00:00",
    )

    assert payload["title"] == "易经起卦记录"
    assert payload["record_id"] == "YJ-TEST0001"
    assert payload["question"] == "此行去山西实习一程怎么样"
    assert payload["method"] == "三枚铜钱法"
    assert payload["has_coins"] is True
    assert payload["cast_trace"]["kind"] == "coin"
    assert payload["primary"] == resolved.primary
    assert payload["changed"] == resolved.changed
    assert payload["primary_text"]
    assert payload["line_rows"]
    assert len(payload["line_rows"]) == 6
    assert payload["line_rows"][0]["position"] == 6
    assert payload["line_rows"][-1]["position"] == 1
    assert [row["label"] for row in payload["line_rows"]] == [
        "上六",
        "九五",
        "六四",
        "九三",
        "六二",
        "初九",
    ]
    assert all(not row["yaoci"].startswith(row["label"]) for row in payload["line_rows"])
    assert [row["is_yang"] for row in payload["line_rows"]] == [
        False,
        True,
        False,
        True,
        False,
        True,
    ]
    assert payload["sources"]


def test_history_payload_supports_empty_records() -> None:
    payload = build_history_payload([])

    assert payload == {"title": "易经历史记录", "items": []}


def test_history_payload_supports_non_empty_records() -> None:
    payload = build_history_payload([_record()])

    assert payload["title"] == "易经历史记录"
    assert len(payload["items"]) == 1
    item = payload["items"][0]
    assert item["id"] == "YJ-TEST0001"
    assert item["question"] == "此行去山西实习一程怎么样"
    assert item["method"] == "三枚铜钱法"
    assert item["primary"]["seq"] == 63
    assert item["changed"]["seq"] == 64
    assert item["moving_positions"] == [3, 4]


def test_record_payload_from_dict_preserves_random_title() -> None:
    data = {
        "id": "YJ-RANDOM01",
        "question": "（未保存原问题）",
        "method": "random",
        "line_values": [7, 7, 7, 7, 7, 7],
        "coins": [],
        "preprocess": {"allowed": True},
        "interpretation": {"summary": "随机摘要"},
        "cast_trace": {"kind": "random", "selected_method": "yarrow"},
        "created_at": "2026-07-08 12:00:00",
    }

    payload = build_record_payload_from_dict(data)

    assert payload["title"] == "随机一卦"


def test_hexagram_query_payload_supports_found_case() -> None:
    payload = build_hexagram_query_payload("乾")

    assert payload["record_id"] == "QUERY"
    assert payload["question"] == "查询：乾"
    assert payload["primary"]["name"] == "乾"
    assert payload["interpretation"]["summary"]


def test_hexagram_query_payload_supports_not_found_case() -> None:
    payload = build_hexagram_query_payload("不存在的卦象")

    assert payload == {"found": False, "query": "不存在的卦象", "title": "解卦结果"}
