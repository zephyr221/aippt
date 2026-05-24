import re

from .constants import MAX_BULLET_CHARS, MAX_BULLETS, MAX_TITLE_CHARS
from .schema import Deck, Layout, Slide


HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$")
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.+?)\s*$")
PAGE_PREFIX_RE = re.compile(r"^第\s*\d+\s*页\s*[·:：\-—]\s*(.+?)\s*$")
COVER_HEADINGS = {"封面", "首页", "标题页"}


def outline_to_deck(markdown: str, title: str | None = None, author: str = "") -> Deck:
    deck_title, cover_notes, sections = _parse_sections(markdown)
    deck_title = _clip(title or deck_title or "Untitled Deck", 120)
    subtitle = _cover_subtitle(cover_notes) or "AI-generated draft"

    slides = [
        Slide(layout=Layout.COVER, title=deck_title, subtitle=subtitle),
    ]
    if len(sections) >= 3:
        slides.append(
            Slide(
                layout=Layout.TOC,
                title="目录",
                bullets=[_clip(section_title, MAX_BULLET_CHARS) for section_title, _ in sections[:6]],
            )
        )
    for section_title, bullets in sections:
        for idx, chunk in enumerate(_chunks(bullets or ["请补充这一页的要点。"], MAX_BULLETS)):
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


def _parse_sections(markdown: str) -> tuple[str | None, list[str], list[tuple[str, list[str]]]]:
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
        if not line:
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
                cover_notes.append(_clean_inline(line))
                continue
            current_title = "主要内容"
        current_bullets.append(_clean_inline(line))

    flush_current()
    return deck_title, cover_notes, sections


def _normalize_heading(heading: str) -> str:
    match = PAGE_PREFIX_RE.match(heading)
    if match:
        heading = match.group(1)
    return heading.strip()


def _is_cover_heading(heading: str) -> bool:
    plain = re.sub(r"[（(].*?[）)]", "", heading).strip()
    return plain in COVER_HEADINGS


def _cover_subtitle(lines: list[str]) -> str:
    useful = [line for line in lines if line and not _is_low_value_cover_line(line)]
    return "\n".join(_clip(line, 70) for line in useful[:4])


def _is_low_value_cover_line(line: str) -> bool:
    return line in {"-", "—", "_"}


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
