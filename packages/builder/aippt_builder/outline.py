import re
from dataclasses import dataclass

from .constants import MAX_BULLET_CHARS, MAX_BULLETS, MAX_TITLE_CHARS
from .schema import Deck, Layout, Slide


HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$")
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.+?)\s*$")
PAGE_PREFIX_RE = re.compile(r"^第\s*\d+\s*页\s*[·:：\-—]\s*(.+?)\s*$")
SLIDE_PREFIX_RE = re.compile(r"^(?:第\s*\d+\s*页|幻灯片\s*\d+)\s*[·:：\-—]\s*(.+?)\s*$")
HORIZONTAL_RULE_RE = re.compile(r"^(?:-{3,}|\*{3,}|_{3,})$")
TABLE_SEPARATOR_RE = re.compile(r"^\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?$")
SPEAKER_NOTES_RE = re.compile(r"^(?:\*\*)?\s*(?:讲者备注|演讲者备注|备注)\s*(?:\*\*)?\s*[：:]")
COVER_HEADINGS = {"封面", "首页", "标题页"}


@dataclass
class ParsedOutline:
    deck_title: str | None
    cover_notes: list[str]
    sections: list[tuple[str, list[str]]]
    explicit_pages: bool = False


def outline_to_deck(markdown: str, title: str | None = None, author: str = "") -> Deck:
    parsed = _parse_sections(markdown)
    title_source = (parsed.deck_title or title) if parsed.explicit_pages else (title or parsed.deck_title)
    deck_title = _clip(title_source or "Untitled Deck", 120)
    subtitle = _cover_subtitle(parsed.cover_notes) or "AI-generated draft"

    slides = [
        Slide(layout=Layout.COVER, title=deck_title, subtitle=subtitle),
    ]
    if len(parsed.sections) >= 3 and not parsed.explicit_pages:
        slides.append(
            Slide(
                layout=Layout.TOC,
                title="目录",
                bullets=[_clip(section_title, MAX_BULLET_CHARS) for section_title, _ in parsed.sections[:MAX_BULLETS]],
            )
        )
    for section_title, bullets in parsed.sections:
        chunks = [bullets[:MAX_BULLETS]] if parsed.explicit_pages else _chunks(bullets or ["请补充这一页的要点。"], MAX_BULLETS)
        for idx, chunk in enumerate(chunks):
            slide_title = section_title if idx == 0 else f"{section_title}（续）"
            slides.append(
                Slide(
                    layout=Layout.ONE_COLUMN,
                    title=_clip(slide_title, MAX_TITLE_CHARS),
                    bullets=[_clip(item, MAX_BULLET_CHARS) for item in chunk],
                )
            )
    if len(slides) == 1:
        slides.append(
            Slide(
                layout=Layout.ONE_COLUMN,
                title="主要内容",
                bullets=["请补充演示主题、受众、目标和关键材料。"],
            )
        )
    slides.append(Slide(layout=Layout.THANKS, title="谢谢"))
    return Deck(title=deck_title, author=author, slides=slides)


def _parse_sections(markdown: str) -> ParsedOutline:
    if _has_explicit_page_headings(markdown):
        return _parse_explicit_pages(markdown)
    return _parse_standard_sections(markdown)


def _parse_standard_sections(markdown: str) -> ParsedOutline:
    deck_title: str | None = None
    cover_notes: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current_bullets: list[str] = []
    current_is_cover = False

    def flush_current() -> None:
        nonlocal current_title, current_bullets, current_is_cover
        if current_title is None:
            return
        if current_is_cover:
            cover_notes.extend(current_bullets)
        else:
            sections.append((current_title, current_bullets))
        current_title = None
        current_bullets = []
        current_is_cover = False

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line or _is_horizontal_rule(line):
            continue

        heading_match = HEADING_RE.match(line)
        if heading_match:
            level = len(heading_match.group(1))
            heading = _normalize_heading(_clean_inline(heading_match.group(2)))
            if level == 1 and deck_title is None:
                deck_title = heading
                continue
            flush_current()
            current_title = heading
            current_bullets = []
            current_is_cover = _is_cover_heading(heading)
            continue

        bullet_match = BULLET_RE.match(line)
        if bullet_match:
            if current_title is None:
                if deck_title:
                    cover_notes.append(_clean_inline(bullet_match.group(1)))
                    continue
                current_title = "主要内容"
            current_bullets.append(_clean_inline(bullet_match.group(1)))
            continue

        if current_title is None:
            if deck_title:
                if not _is_low_value_cover_line(line):
                    cover_notes.append(_clean_inline(line))
                continue
            current_title = "主要内容"
        current_bullets.append(_clean_inline(line))

    flush_current()
    return ParsedOutline(deck_title=deck_title, cover_notes=cover_notes, sections=sections)


def _parse_explicit_pages(markdown: str) -> ParsedOutline:
    deck_title: str | None = None
    cover_notes: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current_lines: list[str] = []
    current_is_cover = False
    seen_page = False
    collecting_lead = True

    def flush_current() -> None:
        nonlocal deck_title, current_title, current_lines, current_is_cover
        if current_title is None:
            return
        if current_is_cover:
            title_from_cover, notes = _extract_cover_from_page(current_lines)
            if title_from_cover and not deck_title:
                deck_title = title_from_cover
            cover_notes.extend(notes)
        else:
            bullets = _extract_page_bullets(current_lines)
            sections.append((current_title, bullets or ["请补充这一页的要点。"]))
        current_title = None
        current_lines = []
        current_is_cover = False

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        heading_match = HEADING_RE.match(line)
        if heading_match:
            heading = _clean_inline(heading_match.group(2))
            page_title = _explicit_page_title(heading)
            if page_title:
                flush_current()
                current_title = _normalize_heading(page_title)
                current_lines = []
                current_is_cover = _is_cover_heading(current_title)
                seen_page = True
                continue
            if not seen_page:
                level = len(heading_match.group(1))
                if level == 1 and deck_title is None:
                    deck_title = _clean_inline(heading)
                    continue
                collecting_lead = False
                continue

        if seen_page:
            current_lines.append(raw_line)
        elif deck_title and collecting_lead and not _is_horizontal_rule(line):
            cover_notes.append(_clean_inline(line.lstrip("> ")))

    flush_current()
    return ParsedOutline(
        deck_title=deck_title,
        cover_notes=cover_notes,
        sections=sections,
        explicit_pages=True,
    )


def _normalize_heading(heading: str) -> str:
    match = PAGE_PREFIX_RE.match(heading)
    if match:
        heading = match.group(1)
    return heading.strip()


def _explicit_page_title(heading: str) -> str | None:
    match = SLIDE_PREFIX_RE.match(heading)
    if match:
        return match.group(1).strip()
    return None


def _has_explicit_page_headings(markdown: str) -> bool:
    count = 0
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        match = HEADING_RE.match(line)
        if match and _explicit_page_title(_clean_inline(match.group(2))):
            count += 1
            if count >= 2:
                return True
    return False


def _is_cover_heading(heading: str) -> bool:
    plain = re.sub(r"[（(].*?[）)]", "", heading).strip()
    return plain in COVER_HEADINGS


def _cover_subtitle(lines: list[str]) -> str:
    useful = [line for line in lines if line and not _is_low_value_cover_line(line)]
    return "\n".join(_clip(line, 70) for line in useful[:4])


def _is_low_value_cover_line(line: str) -> bool:
    return line in {"-", "—", "_"} or _is_horizontal_rule(line)


def _is_horizontal_rule(line: str) -> bool:
    return bool(HORIZONTAL_RULE_RE.match(line.strip()))


def _extract_cover_from_page(lines: list[str]) -> tuple[str | None, list[str]]:
    title: str | None = None
    notes: list[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line or _is_horizontal_rule(line):
            continue
        if BULLET_RE.match(line):
            continue
        heading_match = HEADING_RE.match(line)
        if heading_match and title is None:
            title = _clean_inline(heading_match.group(2))
            continue
        cleaned = _clean_inline(line.lstrip("> "))
        if cleaned and not _is_low_value_cover_line(cleaned):
            notes.append(cleaned)
    return title, notes[:4]


def _extract_page_bullets(lines: list[str]) -> list[str]:
    bullets: list[str] = []
    in_code = False
    skip_notes = False
    for raw_line in lines:
        line = raw_line.strip()
        if not line or _is_horizontal_rule(line):
            continue
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if SPEAKER_NOTES_RE.match(line):
            skip_notes = True
            continue
        if skip_notes:
            continue
        heading_match = HEADING_RE.match(line)
        if heading_match:
            cleaned_heading = _clean_inline(heading_match.group(2))
            if cleaned_heading and not _is_cover_heading(cleaned_heading):
                _append_unique(bullets, cleaned_heading)
            continue
        bullet_match = BULLET_RE.match(line)
        if bullet_match:
            _append_unique(bullets, _clean_inline(bullet_match.group(1)))
            continue
        table_text = _table_row_text(line)
        if table_text:
            _append_unique(bullets, table_text)
            continue
        cleaned = _clean_inline(line.lstrip("> "))
        if cleaned and not _is_low_value_content_line(cleaned):
            _append_unique(bullets, cleaned)
        if len(bullets) >= MAX_BULLETS:
            break
    return bullets[:MAX_BULLETS]


def _table_row_text(line: str) -> str | None:
    if not line.startswith("|") or not line.endswith("|"):
        return None
    if TABLE_SEPARATOR_RE.match(line):
        return None
    cells = [_clean_inline(cell) for cell in line.strip("|").split("|")]
    cells = [cell for cell in cells if cell and not set(cell) <= {"-"}]
    if len(cells) < 2:
        return None
    return "：".join([cells[0], " / ".join(cells[1:])])


def _is_low_value_content_line(line: str) -> bool:
    return (
        line in {"| | |", "|---|---|"}
        or line.startswith("讲者备注")
        or line.startswith("演讲者备注")
        or line.startswith("备注")
    )


def _append_unique(items: list[str], item: str) -> None:
    item = item.strip()
    if item and item not in items:
        items.append(item)




def _clean_inline(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def _clip(text: str, max_chars: int) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _chunks(items: list[str], size: int) -> list[list[str]]:
    return [items[idx : idx + size] for idx in range(0, len(items), size)]
