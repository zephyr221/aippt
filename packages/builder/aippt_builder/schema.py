from enum import StrEnum

from pydantic import BaseModel, Field


class Layout(StrEnum):
    COVER = "cover"
    SECTION = "section"
    TOC = "toc"
    ONE_COLUMN = "one_column"
    TWO_COLUMN = "two_column"
    THREE_COLUMN = "three_column"
    HORIZONTAL = "horizontal"
    COMPARISON = "comparison"
    TABLE = "table"
    SUMMARY = "summary"
    THANKS = "thanks"


class Column(BaseModel):
    heading: str = Field(default="", max_length=60)
    bullets: list[str] = Field(default_factory=list)


class HorizontalItem(BaseModel):
    heading: str = Field(max_length=40)
    desc: str = Field(default="", max_length=80)


class TableData(BaseModel):
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)


class Slide(BaseModel):
    layout: Layout
    title: str = Field(default="", max_length=120)
    subtitle: str = ""
    visual: str | None = Field(default=None, max_length=40)
    proof: str | None = Field(default=None, max_length=120)
    bullets: list[str] = Field(default_factory=list)
    columns: list[Column] = Field(default_factory=list)
    items: list[HorizontalItem] = Field(default_factory=list)
    table: TableData | None = None
    insight: str | None = None


class Deck(BaseModel):
    title: str = Field(max_length=160)
    subtitle: str = ""
    author: str = ""
    slides: list[Slide] = Field(min_length=1)
