from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "nonebot_plugin_yijing" / "data"
DEFAULT_CACHE_DIR = ROOT / "cache" / "wikisource_yijing"

SOURCE_ID = "wikisource_zhouyi"
SOURCE_EDITION = "Wikisource zh-hans HTML page scrape"
SOURCE_USAGE = "Scripted extraction of canonical Zhouyi and Yi Zhuan text."
BASE_URL = "https://zh.wikisource.org/zh-hans/"
USER_AGENT = (
    "nonebot-plugin-yijing-data-script/0.1 "
    "(local corpus collation; https://github.com/newcovid/nonebot-plugin-yijing)"
)

LINE_LABEL_RE = re.compile(r"^(初[九六]|[九六][二三四五]|上[九六])[：，,]")
SPECIAL_LABEL_RE = re.compile(r"^(用[九六])[：，,]")
CHAPTER_TITLE_RE = re.compile(r"^第[一二三四五六七八九十]+章$")
MARKERS = {"易经：", "彖曰：", "象曰：", "文言曰："}
REMOTE_HEXAGRAM_TITLES = {
    "遁": "遯",
}


@dataclass(frozen=True)
class TextBlock:
    tag: str
    text: str


class WikisourceBlockParser(HTMLParser):
    block_tags = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "dd", "dt"}
    skip_tags = {"script", "style", "table", "sup"}
    skip_classes = {"mw-editsection", "noprint", "metadata", "reference"}

    def __init__(self) -> None:
        super().__init__()
        self.in_content = False
        self.content_depth = 0
        self.skip_depth = 0
        self.current_tag: str | None = None
        self.current_parts: list[str] | None = None
        self.blocks: list[TextBlock] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        classes = set(attr_map.get("class", "").split())

        if self.skip_depth:
            if self.in_content:
                self.content_depth += 1
            self.skip_depth += 1
            return

        if tag == "div" and "mw-parser-output" in classes:
            self.in_content = True
            self.content_depth = 1
            return

        if not self.in_content:
            return

        self.content_depth += 1
        if tag in self.skip_tags or self.skip_classes.intersection(classes):
            self.skip_depth = 1
            return

        if tag in self.block_tags:
            self._flush()
            self.current_tag = tag
            self.current_parts = []
        elif tag == "br" and self.current_parts is not None:
            self.current_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if not self.in_content:
            return

        if self.skip_depth:
            self.skip_depth -= 1
            self.content_depth -= 1
            if self.content_depth <= 0:
                self._flush()
                self.in_content = False
            return

        if tag in self.block_tags:
            self._flush()

        self.content_depth -= 1
        if self.content_depth <= 0:
            self._flush()
            self.in_content = False

    def handle_data(self, data: str) -> None:
        if self.in_content and not self.skip_depth and self.current_parts is not None:
            self.current_parts.append(data)

    def _flush(self) -> None:
        if self.current_parts is None:
            return
        text = normalize_text("".join(self.current_parts))
        if text:
            self.blocks.append(TextBlock(self.current_tag or "", text))
        self.current_tag = None
        self.current_parts = None


def normalize_text(text: str) -> str:
    text = unescape(text).replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])", "", text)
    text = re.sub(r"\s+([，。；：？！、」』”）〉])", r"\1", text)
    text = re.sub(r"([「『“（〈])\s+", r"\1", text)
    return normalize_qian_terms(text)


def normalize_qian_terms(text: str) -> str:
    """Repair MediaWiki zh-hans conversion where trigram/hexagram 乾 becomes 干.

    The replacements are deliberately context-bound so Wenyan phrases such as
    "事之干也" and "干事" remain simplified from 幹.
    """

    replacements = {
        "干坤": "乾坤",
        "干元": "乾元",
        "干道": "乾道",
        "干知": "乾知",
        "干以": "乾以",
        "干健": "乾健",
        "干刚": "乾刚",
        "干行": "乾行",
        "干阳": "乾阳",
        "干之策": "乾之策",
        "夫干": "夫乾",
        "乎干": "乎乾",
        "于干": "于乾",
        "诸干": "诸乾",
        "取诸干": "取诸乾",
        "战乎干": "战乎乾",
        "干为": "乾为",
        "干，": "乾，",
        "干。": "乾。",
        "干：": "乾：",
        "干、": "乾、",
    }
    for wrong, right in replacements.items():
        text = text.replace(wrong, right)
    return text


def load_json(name: str) -> Any:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def write_json(name: str, payload: Any) -> None:
    (DATA_DIR / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def wikisource_url(path: str) -> str:
    return BASE_URL + quote(path, safe="/")


def cached_fetch(
    url: str,
    *,
    cache_dir: Path,
    refresh: bool,
    delay_seconds: float,
) -> str:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_name = hashlib.sha256(url.encode("utf-8")).hexdigest() + ".html"
    cache_path = cache_dir / cache_name
    if cache_path.exists() and not refresh:
        return cache_path.read_text(encoding="utf-8")

    time.sleep(delay_seconds)
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=30) as response:
            status = getattr(response, "status", 200)
            if status != 200:
                raise RuntimeError(f"GET {url} returned HTTP {status}")
            html = response.read().decode("utf-8")
    except HTTPError as exc:
        raise RuntimeError(f"GET {url} returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"GET {url} failed: {exc.reason}") from exc

    if "You are making too many requests" in html:
        raise RuntimeError(f"rate limited while fetching {url}")
    cache_path.write_text(html, encoding="utf-8")
    return html


def parse_blocks(html: str) -> list[TextBlock]:
    parser = WikisourceBlockParser()
    parser.feed(html)
    return parser.blocks


def find_marker(blocks: list[str], marker: str) -> int:
    try:
        return blocks.index(marker)
    except ValueError as exc:
        raise ValueError(f"missing marker {marker!r}; got {blocks[:20]!r}") from exc


def join_blocks(blocks: list[str]) -> str:
    return "\n".join(blocks)


def source_locator(hexagram_name: str, layer: str, label: str | None = None) -> str:
    tail = f"/{label}" if label else ""
    return f"周易/{hexagram_name}/{layer}{tail}"


def record_source_fields(locator: str) -> dict[str, str]:
    return {
        "source_id": SOURCE_ID,
        "status": "checked",
        "edition": SOURCE_EDITION,
        "source_locator": locator,
    }


def parse_hexagram_page(
    hexagram: dict[str, Any],
    line_records: list[dict[str, Any]],
    blocks: list[str],
    existing_specials: dict[tuple[int, str], dict[str, Any]],
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, Any] | None,
]:
    seq = int(hexagram["seq"])
    name = str(hexagram["name"])
    yi_index = find_marker(blocks, "易经：")
    tuan_index = find_marker(blocks, "彖曰：")
    xiang_index = find_marker(blocks, "象曰：")
    wenyan_index = blocks.index("文言曰：") if "文言曰：" in blocks else None

    jing_blocks = blocks[yi_index + 1 : tuan_index]
    guaci_blocks: list[str] = []
    line_texts: list[str] = []
    special_texts: list[str] = []
    for block in jing_blocks:
        if LINE_LABEL_RE.match(block):
            line_texts.append(block)
        elif SPECIAL_LABEL_RE.match(block):
            special_texts.append(block)
        else:
            guaci_blocks.append(block)

    if len(line_texts) != 6:
        raise ValueError(f"{seq} {name}: expected 6 line texts, got {len(line_texts)}")
    if not guaci_blocks:
        raise ValueError(f"{seq} {name}: missing guaci")

    guaci = {
        "hexagram_seq": seq,
        "hexagram_name": name,
        "text": join_blocks(guaci_blocks),
        **record_source_fields(source_locator(name, "易经", "卦辞")),
    }

    yaoci: list[dict[str, Any]] = []
    for line_record, text in zip(line_records, line_texts):
        fetched_label = LINE_LABEL_RE.match(text)
        expected_label = str(line_record["line_label"])
        if fetched_label is None or fetched_label.group(1) != expected_label:
            raise ValueError(
                f"{seq} {name}: expected {expected_label}, got {text[:20]!r}"
            )
        yaoci.append(
            {
                "hexagram_seq": seq,
                "position": int(line_record["position"]),
                "line_label": expected_label,
                "text": text,
                **record_source_fields(source_locator(name, "易经", expected_label)),
            }
        )

    tuan_blocks = blocks[tuan_index + 1 : xiang_index]
    if not tuan_blocks:
        raise ValueError(f"{seq} {name}: missing tuan")
    tuan = {
        "hexagram_seq": seq,
        "hexagram_name": name,
        "text": join_blocks(tuan_blocks),
        **record_source_fields(source_locator(name, "彖")),
    }

    xiang_end = wenyan_index if wenyan_index is not None else len(blocks)
    xiang_blocks = blocks[xiang_index + 1 : xiang_end]
    if len(xiang_blocks) < 7:
        raise ValueError(f"{seq} {name}: expected daxiang + 6 xiaoxiang records")
    daxiang_text = xiang_blocks[0]
    xiaoxiang_texts = xiang_blocks[1:7]
    special_xiang_texts = xiang_blocks[7:]
    xiang = {
        "hexagram_seq": seq,
        "hexagram_name": name,
        "daxiang": daxiang_text,
        "daxiang_source_id": SOURCE_ID,
        "daxiang_status": "checked",
        "daxiang_edition": SOURCE_EDITION,
        "daxiang_source_locator": source_locator(name, "象", "大象"),
        "xiaoxiang": [],
        "source_id": SOURCE_ID,
        "status": "checked",
        "edition": SOURCE_EDITION,
        "source_locator": source_locator(name, "象"),
    }
    for line_record, text in zip(line_records, xiaoxiang_texts):
        label = str(line_record["line_label"])
        xiang["xiaoxiang"].append(
            {
                "position": int(line_record["position"]),
                "line_label": label,
                "text": text,
                "source_id": SOURCE_ID,
                "status": "checked",
                "edition": SOURCE_EDITION,
                "source_locator": source_locator(name, "象", label),
            }
        )

    special_records: list[dict[str, Any]] = []
    special_xiang_by_label: dict[str, str] = {}
    for text in special_xiang_texts:
        if text.startswith("用九"):
            special_xiang_by_label["用九"] = text
        elif text.startswith("用六"):
            special_xiang_by_label["用六"] = text

    for text in special_texts:
        match = SPECIAL_LABEL_RE.match(text)
        if match is None:
            raise ValueError(f"{seq} {name}: malformed special text {text!r}")
        label = match.group(1)
        existing = dict(existing_specials.get((seq, label), {}))
        special = {
            **existing,
            "id": existing.get("id") or f"{name}_{label}",
            "hexagram_seq": seq,
            "hexagram_name": name,
            "label": label,
            "kind": "special_line_text",
            "text": text,
            **record_source_fields(source_locator(name, "易经", label)),
        }
        if label in special_xiang_by_label:
            special.update(
                {
                    "xiang_text": special_xiang_by_label[label],
                    "xiang_source_id": SOURCE_ID,
                    "xiang_status": "checked",
                    "xiang_edition": SOURCE_EDITION,
                    "xiang_source_locator": source_locator(name, "象", label),
                }
            )
        special_records.append(special)

    wenyan = None
    if wenyan_index is not None:
        wenyan_blocks = blocks[wenyan_index + 1 :]
        if not wenyan_blocks:
            raise ValueError(f"{seq} {name}: missing wenyan")
        wenyan = {
            "hexagram_seq": seq,
            "hexagram_name": name,
            "scope": "canonical_wenyan",
            "text": join_blocks(wenyan_blocks),
            "sections": [
                {"order": order, "text": text}
                for order, text in enumerate(wenyan_blocks, start=1)
            ],
            **record_source_fields(source_locator(name, "文言")),
        }

    return guaci, yaoci, tuan, xiang, special_records, wenyan


def is_chapter_title(block: TextBlock) -> bool:
    return block.tag in {"h2", "h3"} and (
        bool(CHAPTER_TITLE_RE.match(block.text)) or block.text in {"上篇", "下篇", "一篇"}
    )


def parse_chapter_page(page_path: str, blocks: list[TextBlock]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current_title: str | None = None
    current_text: list[str] = []

    def flush() -> None:
        nonlocal current_title, current_text
        if current_title is None:
            return
        if not current_text:
            raise ValueError(f"{page_path}: empty chapter {current_title}")
        records.append(
            {
                "chapter": len(records) + 1,
                "title": current_title,
                "text": join_blocks(current_text),
                **record_source_fields(f"{page_path}#{current_title}"),
            }
        )
        current_title = None
        current_text = []

    for block in blocks:
        if is_chapter_title(block):
            flush()
            current_title = block.text
            current_text = []
        elif current_title is not None and block.text not in MARKERS:
            current_text.append(block.text)

    flush()
    if not records:
        raise ValueError(f"{page_path}: no chapter records parsed")
    return records


def build_sources(existing_sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sources = [dict(item) for item in existing_sources]
    for item in sources:
        if item["id"] == SOURCE_ID:
            item.update(
                {
                    "name": "维基文库《周易》",
                    "title": "周易",
                    "type": "classical_text",
                    "url": "https://zh.wikisource.org/zh-hans/周易",
                    "edition": SOURCE_EDITION,
                    "license": "Public domain source text; Wikisource page text under CC BY-SA 4.0.",
                    "usage": SOURCE_USAGE,
                    "notes": (
                        "Corpus text is extracted by scripts/fetch_wikisource_corpus.py "
                        "from public Wikisource pages and normalized structurally; no AI "
                        "generation is used for corpus text."
                    ),
                }
            )
            break
    else:
        sources.append(
            {
                "id": SOURCE_ID,
                "name": "维基文库《周易》",
                "title": "周易",
                "type": "classical_text",
                "url": "https://zh.wikisource.org/zh-hans/周易",
                "edition": SOURCE_EDITION,
                "license": "Public domain source text; Wikisource page text under CC BY-SA 4.0.",
                "usage": SOURCE_USAGE,
                "notes": (
                    "Corpus text is extracted by scripts/fetch_wikisource_corpus.py "
                    "from public Wikisource pages and normalized structurally; no AI "
                    "generation is used for corpus text."
                ),
            }
        )
    return sources


def build_corpus(args: argparse.Namespace) -> None:
    hexagrams = load_json("hexagrams.json")
    lines = load_json("lines.json")
    existing_specials = {
        (int(item["hexagram_seq"]), str(item["label"])): item
        for item in load_json("special_texts.json")
    }
    lines_by_hexagram: dict[int, list[dict[str, Any]]] = {}
    for line in lines:
        lines_by_hexagram.setdefault(int(line["hexagram_seq"]), []).append(line)
    for values in lines_by_hexagram.values():
        values.sort(key=lambda item: int(item["position"]))

    guaci_records: list[dict[str, Any]] = []
    yaoci_records: list[dict[str, Any]] = []
    tuan_records: list[dict[str, Any]] = []
    xiang_records: list[dict[str, Any]] = []
    special_records: list[dict[str, Any]] = []
    wenyan_records: list[dict[str, Any]] = []

    for hexagram in hexagrams:
        name = str(hexagram["name"])
        remote_name = REMOTE_HEXAGRAM_TITLES.get(name, name)
        url = wikisource_url(f"周易/{remote_name}")
        html = cached_fetch(
            url,
            cache_dir=args.cache_dir,
            refresh=args.refresh,
            delay_seconds=args.delay,
        )
        blocks = [block.text for block in parse_blocks(html)]
        parsed = parse_hexagram_page(
            hexagram,
            lines_by_hexagram[int(hexagram["seq"])],
            blocks,
            existing_specials,
        )
        guaci, yaoci, tuan, xiang, specials, wenyan = parsed
        guaci_records.append(guaci)
        yaoci_records.extend(yaoci)
        tuan_records.append(tuan)
        xiang_records.append(xiang)
        special_records.extend(specials)
        if wenyan is not None:
            wenyan_records.append(wenyan)

    chapter_pages = {
        "xici_shang.json": "周易/繫辭上",
        "xici_xia.json": "周易/繫辭下",
        "shuogua.json": "周易/說卦",
        "xugua.json": "周易/序卦",
        "zagua.json": "周易/雜卦",
    }
    chapter_payloads: dict[str, list[dict[str, Any]]] = {}
    for filename, page_path in chapter_pages.items():
        html = cached_fetch(
            wikisource_url(page_path),
            cache_dir=args.cache_dir,
            refresh=args.refresh,
            delay_seconds=args.delay,
        )
        chapter_payloads[filename] = parse_chapter_page(page_path, parse_blocks(html))

    validate_payloads(
        guaci_records,
        yaoci_records,
        tuan_records,
        xiang_records,
        special_records,
        wenyan_records,
        chapter_payloads,
    )

    if args.dry_run:
        print(
            "parsed "
            f"{len(guaci_records)} guaci, "
            f"{len(yaoci_records)} yaoci, "
            f"{len(tuan_records)} tuan, "
            f"{len(xiang_records)} xiang, "
            f"{len(wenyan_records)} wenyan, "
            f"{len(special_records)} special texts"
        )
        for filename, records in chapter_payloads.items():
            print(f"parsed {len(records)} chapter records for {filename}")
        return

    write_json("guaci.json", guaci_records)
    write_json("yaoci.json", yaoci_records)
    write_json("tuan.json", tuan_records)
    write_json("xiang.json", xiang_records)
    write_json("wenyan.json", wenyan_records)
    write_json("special_texts.json", special_records)
    for filename, records in chapter_payloads.items():
        write_json(filename, records)
    write_json("sources.json", build_sources(load_json("sources.json")))


def validate_payloads(
    guaci_records: list[dict[str, Any]],
    yaoci_records: list[dict[str, Any]],
    tuan_records: list[dict[str, Any]],
    xiang_records: list[dict[str, Any]],
    special_records: list[dict[str, Any]],
    wenyan_records: list[dict[str, Any]],
    chapter_payloads: dict[str, list[dict[str, Any]]],
) -> None:
    if len(guaci_records) != 64:
        raise ValueError(f"expected 64 guaci records, got {len(guaci_records)}")
    if len(yaoci_records) != 384:
        raise ValueError(f"expected 384 yaoci records, got {len(yaoci_records)}")
    if len(tuan_records) != 64:
        raise ValueError(f"expected 64 tuan records, got {len(tuan_records)}")
    if len(xiang_records) != 64:
        raise ValueError(f"expected 64 xiang records, got {len(xiang_records)}")
    if len(special_records) != 2:
        raise ValueError(f"expected 2 special texts, got {len(special_records)}")
    if {int(item["hexagram_seq"]) for item in wenyan_records} != {1, 2}:
        raise ValueError("wenyan must be scoped to Qian and Kun only")

    for item in xiang_records:
        if len(item["xiaoxiang"]) != 6:
            raise ValueError(f"{item['hexagram_name']}: expected 6 xiaoxiang records")

    for filename, records in chapter_payloads.items():
        if not records:
            raise ValueError(f"{filename}: no chapter records")

    encoded = json.dumps(
        {
            "guaci": guaci_records,
            "yaoci": yaoci_records,
            "tuan": tuan_records,
            "xiang": xiang_records,
            "special": special_records,
            "wenyan": wenyan_records,
            "chapters": chapter_payloads,
        },
        ensure_ascii=False,
    )
    if "待补录" in encoded or "placeholder" in encoded:
        raise ValueError("scraped payload still contains placeholder text/status")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch public Wikisource Zhouyi/Yi Zhuan text into package JSON data."
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=DEFAULT_CACHE_DIR,
        help="HTML response cache directory. Defaults to the ignored repo cache/ tree.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Ignore cached HTML and re-fetch Wikisource pages.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.35,
        help="Delay in seconds before each network request when cache is missed.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate without writing data files.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    build_corpus(parse_args())
