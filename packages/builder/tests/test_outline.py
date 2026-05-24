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
    assert [slide.title for slide in deck.slides[1:4]] == [
        "开场：一个事实",
        "我们为什么需要工作流",
        "下一步",
    ]
    assert all("第 " not in slide.title for slide in deck.slides[1:-1])
    assert all("封面" not in slide.title for slide in deck.slides[1:-1])
    assert validate_deck(deck) == []


def test_outline_limits_toc_to_valid_bullet_count() -> None:
    markdown = "# Long Deck\n\n" + "\n\n".join(
        f"## Section {idx}\n\n- Point {idx}" for idx in range(1, 8)
    )

    deck = outline_to_deck(markdown)

    assert deck.slides[1].layout == "toc"
    assert len(deck.slides[1].bullets) == 5
    assert validate_deck(deck) == []


def test_explicit_page_outline_ignores_planning_notes_and_speaker_notes() -> None:
    deck = outline_to_deck(
        """# AI × 计算材料科研：2026 年春，你需要知道的事

> 面向 SJTU 计算材料课题组（DFT / MD）的组会分享
> 2026 年 3 月 27 日（周五）

---

## 我的整体思路

1. 这段是给讲者看的设计说明，不应该生成正文页。
2. 继续说明为什么要这样编排。

---

## 第 1 页 · 封面

# AI × 计算材料科研
**2026 年春，你需要知道的事**

副标题：从对话到自主科研 Agent——理解当前 AI，用好当前 AI

---

## 第 2 页 · 开场：一个事实

**三年前的今天，GPT-4 刚发布两周。**
**上周，一个 AI Agent 独自花了几天，从零写出了一个宇宙学 Boltzmann 求解器。**

- 2023.03.14 — GPT-4 发布
- 2026.03.23 — Claude 自主完成 Boltzmann solver
- 这类数值求解器，人类专家通常需要数月到数年

> 三年。从“能聊天”到“能独立做数值计算科研”。

**讲者备注**：
开场不讲道理，讲事实。这段不应进入 PPT 正文。

---

## 第 3 页 · AI 正在发生什么：一分钟理解核心脉络

| 阶段 | 环境 | 验证信号 |
|---|---|---|
| 早期 LLM | 无 | 人工标注 |
| Agent（当前） | 真实计算环境 | 任务是否完成 |

```text
这段 ASCII 图不应被当成 bullet。
```

> 对做 DFT/MD 的人来说，关键信息是精确验证。
""",
        author="AIPPT",
    )

    assert [slide.title for slide in deck.slides] == [
        "AI × 计算材料科研：2026 年春，你需要知道的事",
        "开场：一个事实",
        "AI 正在发生什么：一分钟理解核心脉络",
        "谢谢",
    ]
    body_text = "\n".join("\n".join(slide.bullets) for slide in deck.slides)
    assert "我的整体思路" not in body_text
    assert "讲者备注" not in body_text
    assert "ASCII 图" not in body_text
    assert "Agent（当前）" in body_text
    assert validate_deck(deck) == []
