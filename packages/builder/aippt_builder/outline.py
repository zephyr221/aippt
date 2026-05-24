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
CHINESE_NUMBERS = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}


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
    if _looks_like_brief_prompt(markdown):
        return _parse_brief_prompt(markdown)
    if _has_explicit_page_headings(markdown):
        return _parse_explicit_pages(markdown)
    return _parse_standard_sections(markdown)


def _looks_like_brief_prompt(markdown: str) -> bool:
    lines = [line.strip() for line in markdown.splitlines() if line.strip()]
    if not lines or len(lines) > 2:
        return False
    joined = " ".join(lines)
    if HEADING_RE.search(joined) or BULLET_RE.search(joined) or "|" in joined:
        return False
    return len(joined) <= 120 and bool(
        re.search(r"(PPT|ppt|幻灯片|页|关于|科普|介绍|分享|报告|讲讲|做|制作|生成)", joined)
    )


def _parse_brief_prompt(prompt: str) -> ParsedOutline:
    cleaned_prompt = _clean_inline(
        " ".join(line.strip() for line in prompt.splitlines() if line.strip())
    )
    total_pages = _requested_page_count(cleaned_prompt)
    topic = _prompt_topic(cleaned_prompt)
    deck_title = _prompt_deck_title(topic, cleaned_prompt)
    body_pages = max(2, total_pages - 2)
    sections = _prompt_sections(topic, body_pages)
    return ParsedOutline(
        deck_title=deck_title,
        cover_notes=[
            f"用 {total_pages} 页讲清楚：是什么、怎么工作、有什么用、边界在哪里。",
            "由一句话需求自动规划，可继续编辑大纲。",
        ],
        sections=sections,
        explicit_pages=True,
    )


def _requested_page_count(prompt: str) -> int:
    digit_range = re.search(r"(\d{1,2})\s*(?:[-~到至]|—)\s*(\d{1,2})\s*页", prompt)
    if digit_range:
        return _clamp_page_count(int(digit_range.group(2)))

    digit_single = re.search(r"(\d{1,2})\s*页", prompt)
    if digit_single:
        return _clamp_page_count(int(digit_single.group(1)))

    zh_range = re.search(
        r"([一二两三四五六七八九十]{1,3})\s*(?:到|至|[-~—])\s*"
        r"([一二两三四五六七八九十]{1,3})\s*页",
        prompt,
    )
    if zh_range:
        return _clamp_page_count(_chinese_number(zh_range.group(2)) or 6)

    zh_pair = re.search(r"([一二两三四五六七八九])([一二两三四五六七八九])\s*页", prompt)
    if zh_pair:
        return _clamp_page_count(CHINESE_NUMBERS[zh_pair.group(2)])

    zh_single = re.search(r"([一二两三四五六七八九十]{1,3})\s*页", prompt)
    if zh_single:
        return _clamp_page_count(_chinese_number(zh_single.group(1)) or 6)

    return 6


def _clamp_page_count(value: int) -> int:
    return min(12, max(4, value))


def _chinese_number(value: str) -> int | None:
    if value in CHINESE_NUMBERS:
        return CHINESE_NUMBERS[value]
    if value.startswith("十") and len(value) == 2:
        return 10 + CHINESE_NUMBERS.get(value[1], 0)
    if value.endswith("十") and len(value) == 2:
        return CHINESE_NUMBERS.get(value[0], 0) * 10
    if "十" in value and len(value) == 3:
        return CHINESE_NUMBERS.get(value[0], 0) * 10 + CHINESE_NUMBERS.get(value[2], 0)
    return None


def _prompt_topic(prompt: str) -> str:
    topic_match = re.search(
        r"关于\s*(.+?)(?:的)?(?:科普|介绍|分享|报告|PPT|ppt|幻灯片|$)",
        prompt,
    )
    if topic_match:
        return _clean_prompt_topic(topic_match.group(1))

    topic = re.sub(r"\d{1,2}\s*(?:[-~到至]|—)?\s*\d{0,2}\s*页", " ", prompt)
    topic = re.sub(
        r"[一二两三四五六七八九十]{1,3}\s*(?:到|至|[-~—])?"
        r"\s*[一二两三四五六七八九十]{0,3}\s*页",
        " ",
        topic,
    )
    topic = re.sub(
        r"(请|帮我|可否|能否|可以|课否|做|制作|生成|写|来|一个|一份|左右|"
        r"大概|大约|PPT|ppt|幻灯片|页面|关于|为企业|面向企业|给企业|科普|介绍|分享|报告|啊|吧|呢)",
        " ",
        topic,
    )
    return _clean_prompt_topic(topic)


def _clean_prompt_topic(topic: str) -> str:
    topic = re.sub(r"[，,。.!！?？:：；;、]+", " ", topic)
    topic = re.sub(r"\s+", " ", topic).strip(" 的")
    return _clip(topic or "主题演示", 30)


def _prompt_deck_title(topic: str, prompt: str) -> str:
    if "科普" in prompt and not topic.endswith("科普"):
        return _clip(f"{topic}科普", 60)
    return _clip(topic, 60)


def _prompt_sections(topic: str, body_pages: int) -> list[tuple[str, list[str]]]:
    candidates = [
        (
            "为什么值得了解",
            [
                f"{topic}已经进入学习、工作和科研工具链，关键是理解它能做什么、不能替人做什么。",
                "技术位置：它不再只是实验室概念；搜索、推荐、图像识别和语音转写都在使用；很多办公与科研工具已把它作为默认能力。",
                "学习价值：它让计算机从历史样本中总结可复用规律；适合处理规则难以手写的问题；能把数据经验转化成预测、分类或生成能力。",
                "使用边界：结果依赖数据质量和任务定义；训练集表现好不等于真实世界可靠；上线后仍需要新样本验证、人工审查和反馈闭环。",
            ],
        ),
        (
            "一句话理解",
            [
                f"{topic}的核心，是让计算机从数据中发现规律，并把规律用于新情境。",
                "输入：把图片、文字、表格或传感器记录变成特征；特征需要保留与任务有关的信息；噪声、缺失值和偏差会直接影响学习效果。",
                "学习：模型根据样本反复做预测；把预测结果与真实标签或反馈比较；再调整内部参数，让下一次预测更接近目标。",
                "输出：常见结果是概率、排序、分类或生成内容；输出不是绝对真理；真正价值取决于能否帮助人更快决策或完成任务。",
            ],
        ),
        (
            "它如何工作",
            [
                "典型流程是数据准备、模型训练、效果评估和迭代改进，四步缺一不可。",
                "数据准备：收集样本并清洗异常值；把输入表示为特征 x；把监督信号整理成标签 y 或可比较的反馈。",
                "模型训练：用 ŷ=fθ(x) 产生预测；根据误差调整参数 θ；训练目标不是记住样本，而是学到可迁移的规律。",
                "公式：J(θ)=1/m ∑ᵢ L(yᵢ, fθ(xᵢ))，训练就是让 J(θ) 变小。",
                "效果评估：保留测试集检查泛化能力；比较准确率、召回率或业务指标；发现失败样例后回到数据和模型继续迭代。",
            ],
        ),
        (
            "身边的应用",
            [
                f"{topic}的应用通常不是单独存在，而是嵌入具体流程，帮助人更快发现、判断和生成。",
                "学习场景：根据练习记录推荐下一道题；识别知识薄弱点；把长材料摘要成适合复习的结构化笔记。",
                "科研场景：从实验和模拟数据中发现模式；辅助筛选候选方案；把文献检索、数据分析和报告写作连成工作流。",
                "办公场景：自动摘要、分类、检索和内容生成降低重复劳动；结合审批与人工复核；让人把时间放在判断、沟通和创造上。",
            ],
        ),
        (
            "常见误区",
            [
                "模型不是万能答案机，越接近真实业务，越需要清晰验证和责任边界。",
                "数据误区：训练集表现好不代表真实世界可靠；样本偏差会被模型继承甚至放大；数据来源、标注质量和时间变化都要记录。",
                "模型误区：模型越大不一定越适合；还要看成本、延迟、部署和维护；简单模型在可解释任务上可能更稳。",
                "评价误区：准确率之外还要看召回率、公平性、隐私和可解释性；面向人的系统必须设计人工确认、回滚和申诉机制。",
            ],
        ),
        (
            "如何继续学习",
            [
                "学习路线可以从概念到小实验，再到真实问题，重点是形成验证习惯。",
                "概念入门：先掌握数据、特征、训练、测试四个关键词；理解过拟合、泛化和损失函数；把每个术语放回具体任务中理解。",
                "工具实践：用小数据集跑通训练和评估；从 scikit-learn 开始，再理解 PyTorch/JAX；记录每次实验的假设、指标和失败原因。",
                "问题判断：关注模型能否解决真实问题；比较人工规则、传统模型和大模型方案；不要只追逐名词，要看数据闭环是否成立。",
            ],
        ),
    ]
    return candidates[:body_pages]


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
