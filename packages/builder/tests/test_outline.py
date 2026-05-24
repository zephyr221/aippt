import json

from aippt_builder.outline import outline_to_deck
from aippt_builder.validate import validate_deck


def test_outline_to_deck_creates_valid_buildable_ir() -> None:
    deck = outline_to_deck(
        """# AI PPT

## 背景

- 多用户登录
- 独立 PPT 工作区

## 生成链路

- Markdown outline
- Deck IR
- PPTX artifact
""",
        author="AIPPT",
    )

    assert deck.title == "AI PPT"
    assert deck.slides[0].layout == "cover"
    assert deck.slides[-1].layout == "thanks"
    assert validate_deck(deck) == []

    payload = json.loads(deck.model_dump_json())
    assert payload["slides"][1]["title"] == "背景"
    assert payload["slides"][2]["bullets"] == ["Markdown outline", "Deck IR", "PPTX artifact"]


def test_outline_promotes_cover_metadata_and_normalizes_page_headings() -> None:
    deck = outline_to_deck(
        """# AI × 计算材料科研

2026 年春，你需要知道的事
副标题：从对话到自主科研 Agent——理解当前 AI，用好当前 AI
SJTU · 计算材料课程组 组会分享
2026.03.27

## 第 1 页 · 封面

- 这行是旧封面备注，不应该生成正文页

## 第 2 页 · 开场：一个事实

- 三年前的今天，GPT-4 刚刚被看见
- 今天 Agent 已经能够拆解任务、调用工具、生成材料

## 第 3 页 · 我们为什么需要工作流

- 让生成过程可复现
- 让结果可以审阅、修复和下载

## 第 4 页 · 下一步

- 接入更强的 Agent 核心
- 加入模板和预览
""",
        author="AIPPT",
    )

    assert deck.slides[0].layout == "cover"
    assert "2026 年春" in deck.slides[0].subtitle
    assert "旧封面备注" not in deck.slides[0].subtitle
    assert deck.slides[1].layout == "toc"
    assert [slide.title for slide in deck.slides[2:5]] == [
        "开场：一个事实",
        "我们为什么需要工作流",
        "下一步",
    ]
    assert all("第 " not in slide.title for slide in deck.slides[1:-1])
    assert all("封面" not in slide.title for slide in deck.slides[1:-1])
    assert validate_deck(deck) == []
