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
