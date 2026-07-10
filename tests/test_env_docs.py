from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSIGNMENT = re.compile(r"^(?:# )?([A-Z][A-Z0-9_]*)=")


def _env_block(markdown: str, heading: str) -> str:
    marker = f"### {heading}\n\n```env\n"
    return markdown.split(marker, 1)[1].split("\n```", 1)[0]


def _keys(text: str) -> set[str]:
    return {match.group(1) for line in text.splitlines() if (match := ASSIGNMENT.match(line))}


def _assert_every_field_has_comment(text: str) -> None:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not ASSIGNMENT.match(line):
            continue
        assert index > 0, line
        comment = lines[index - 1]
        assert comment.startswith("# "), line
        assert not ASSIGNMENT.match(comment), line


def test_env_example_and_readme_samples_are_fully_commented_and_in_sync() -> None:
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    readme_cn = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_en = (ROOT / "README.en.md").read_text(encoding="utf-8")
    samples = [
        env_example,
        _env_block(readme_cn, "ENV 示例"),
        _env_block(readme_en, "ENV sample"),
    ]

    for sample in samples:
        _assert_every_field_has_comment(sample)

    expected = _keys(env_example)
    assert expected
    assert _keys(samples[1]) == expected
    assert _keys(samples[2]) == expected
