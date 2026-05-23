from dataclasses import dataclass

import regex

from .constants import MAX_BULLET_CHARS, MAX_BULLETS, MAX_TITLE_CHARS
from .schema import Deck, Layout, Slide


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str


def display_len(text: str) -> int:
    """Approximate display length, counting CJK characters as one unit."""
    return len(regex.findall(r"\X", text or ""))


def validate_deck(deck: Deck) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for idx, slide in enumerate(deck.slides):
        issues.extend(validate_slide(slide, f"slides[{idx}]"))
    return issues


def validate_slide(slide: Slide, path: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if slide.layout not in {Layout.COVER, Layout.THANKS} and not slide.title.strip():
        issues.append(ValidationIssue(path=f"{path}.title", message="content slides need a title"))
    if display_len(slide.title) > MAX_TITLE_CHARS and slide.layout not in {Layout.COVER, Layout.THANKS}:
        issues.append(
            ValidationIssue(
                path=f"{path}.title",
                message=f"title should be <= {MAX_TITLE_CHARS} characters",
            )
        )
    if len(slide.bullets) > MAX_BULLETS:
        issues.append(
            ValidationIssue(path=f"{path}.bullets", message=f"at most {MAX_BULLETS} bullets")
        )
    for bullet_idx, bullet in enumerate(slide.bullets):
        if display_len(bullet) > MAX_BULLET_CHARS:
            issues.append(
                ValidationIssue(
                    path=f"{path}.bullets[{bullet_idx}]",
                    message=f"bullet should be <= {MAX_BULLET_CHARS} characters",
                )
            )
    if slide.layout == Layout.TABLE and slide.table:
        if len(slide.table.rows) > 5 or len(slide.table.headers) > 4:
            issues.append(
                ValidationIssue(path=f"{path}.table", message="table should be at most 5x4")
            )
    return issues

