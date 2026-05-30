import re
from dataclasses import dataclass

from .constants import MAX_BULLET_CHARS, MAX_BULLETS, MAX_TITLE_CHARS
from .schema import Column, Deck, HorizontalItem, Layout, Slide, TableData


HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$")
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.+?)\s*$")
PAGE_PREFIX_RE = re.compile(r"^第\s*\d+\s*页\s*[·:：\-—]\s*(.+?)\s*$")
SLIDE_PREFIX_RE = re.compile(r"^(?:第\s*\d+\s*页|幻灯片\s*\d+)\s*[·:：\-—]\s*(.+?)\s*$")
HORIZONTAL_RULE_RE = re.compile(r"^(?:-{3,}|\*{3,}|_{3,})$")
TABLE_SEPARATOR_RE = re.compile(r"^\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?$")
SPEAKER_NOTES_RE = re.compile(r"^(?:\*\*)?\s*(?:讲者备注|演讲者备注|备注)\s*(?:\*\*)?\s*[：:]")
CONTENT_LABEL_RE = re.compile(r"^(?:一句话|核心判断|核心结论|本页核心判断)\s*[：:]\s*")
LAYOUT_LABEL_RE = re.compile(r"^(?:版式|布局|layout)\s*[：:]\s*(.+?)\s*$", re.IGNORECASE)
VISUAL_LABEL_RE = re.compile(
    r"^(?:组件|视觉|visual|component)\s*[：:]\s*(.+?)\s*$",
    re.IGNORECASE,
)
INSIGHT_LABEL_RE = re.compile(
    r"^(?:洞察|insight|核心提示|页面提示|底部提示)\s*[：:]\s*(.+?)\s*$",
    re.IGNORECASE,
)
SUPPORT_LABEL_RE = re.compile(
    r"^(?:支撑|展开|展开方式|展开对象|细化|依据|案例|例子|证据|证明|support|detail|proof|proof object|证据对象)\s*[：:]\s*(.+?)\s*$",
    re.IGNORECASE,
)
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
LAYOUT_ALIASES = {
    "cover": Layout.COVER,
    "封面": Layout.COVER,
    "section": Layout.SECTION,
    "章节": Layout.SECTION,
    "目录": Layout.TOC,
    "toc": Layout.TOC,
    "one_column": Layout.ONE_COLUMN,
    "single": Layout.ONE_COLUMN,
    "单栏": Layout.ONE_COLUMN,
    "正文": Layout.ONE_COLUMN,
    "two_column": Layout.TWO_COLUMN,
    "two-columns": Layout.TWO_COLUMN,
    "双栏": Layout.TWO_COLUMN,
    "左右栏": Layout.TWO_COLUMN,
    "three_column": Layout.THREE_COLUMN,
    "three-columns": Layout.THREE_COLUMN,
    "三栏": Layout.THREE_COLUMN,
    "horizontal": Layout.HORIZONTAL,
    "横向": Layout.HORIZONTAL,
    "流程": Layout.HORIZONTAL,
    "阶段": Layout.HORIZONTAL,
    "comparison": Layout.COMPARISON,
    "对比": Layout.COMPARISON,
    "table": Layout.TABLE,
    "表格": Layout.TABLE,
    "summary": Layout.SUMMARY,
    "总结": Layout.SUMMARY,
    "thanks": Layout.THANKS,
    "致谢": Layout.THANKS,
}
VISUAL_ALIASES = {
    "cards": "card_grid",
    "card_grid": "card_grid",
    "卡片": "card_grid",
    "卡片组": "card_grid",
    "rich_cards": "rich_cards",
    "rich_card_grid": "rich_cards",
    "详实卡片": "rich_cards",
    "多要点卡片": "rich_cards",
    "fact_grid": "fact_grid",
    "facts": "fact_grid",
    "事实块": "fact_grid",
    "事实卡": "fact_grid",
    "timeline": "timeline",
    "时间线": "timeline",
    "process": "process",
    "process_cards": "process",
    "流程卡": "process",
    "流程图": "process",
    "concept_diagram": "concept_diagram",
    "concept_map": "concept_diagram",
    "diagram": "concept_diagram",
    "map": "concept_diagram",
    "概念图": "concept_diagram",
    "结构图": "concept_diagram",
    "图解": "concept_diagram",
    "关系图": "concept_diagram",
    "example_walkthrough": "example_walkthrough",
    "worked_example": "example_walkthrough",
    "case_walkthrough": "example_walkthrough",
    "案例讲解": "example_walkthrough",
    "案例拆解": "example_walkthrough",
    "例题讲解": "example_walkthrough",
    "two_column": "two_column",
    "双栏": "two_column",
    "three_column": "three_column",
    "三栏": "three_column",
    "horizontal": "horizontal",
    "横向": "horizontal",
    "table": "table",
    "表格": "table",
    "summary": "summary",
    "总结": "summary",
    "stat": "stat_callout",
    "stats": "stat_callout",
    "stat_callout": "stat_callout",
    "kpi": "stat_callout",
    "kpi_cards": "stat_callout",
    "指标卡": "stat_callout",
    "大数字": "stat_callout",
    "quote": "quote_block",
    "quote_block": "quote_block",
    "引用": "quote_block",
    "金句": "quote_block",
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
        chunks = [bullets] if parsed.explicit_pages else _chunks(bullets or ["请补充这一页的要点。"], MAX_BULLETS)
        for idx, chunk in enumerate(chunks):
            slide_title = section_title if idx == 0 else f"{section_title}（续）"
            slides.append(_slide_from_section(slide_title, chunk))
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
    sections = _prompt_sections(topic, body_pages, cleaned_prompt)
    return ParsedOutline(
        deck_title=deck_title,
        cover_notes=[
            f"用 {total_pages} 页讲清楚：是什么、怎么工作、有什么用、边界在哪里。",
            "由简短需求自动规划，可继续编辑大纲。",
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

    if re.search(r"(导论|入门|课程|教学|培训|学习|科普)", prompt):
        return 8
    if re.search(r"(项目|汇报|报告|研究|申报|产品|方案)", prompt):
        return 7
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


def _prompt_sections(topic: str, body_pages: int, prompt: str) -> list[tuple[str, list[str]]]:
    kind = _prompt_kind(topic, prompt)
    if kind == "teaching":
        return _teaching_sections(topic, body_pages)
    if kind == "project":
        return _project_sections(topic, body_pages)
    if kind == "research":
        return _research_sections(topic, body_pages)
    if kind == "product":
        return _product_sections(topic, body_pages)
    return _general_sections(topic, body_pages)


def _prompt_kind(topic: str, prompt: str) -> str:
    text = f"{topic} {prompt}"
    if re.search(r"(研究|论文|课题|基金|申报|实验|方法|结果|科研)", text):
        return "research"
    if re.search(r"(产品|方案|客户|市场|销售|发布|商业|能力介绍)", text):
        return "product"
    if re.search(r"(项目|进展|复盘|周报|月报|汇报|报告|里程碑|风险)", text):
        return "project"
    if re.search(r"(导论|入门|课程|教学|培训|学习|科普|初学|课堂)", text):
        return "teaching"
    return "general"


def _teaching_sections(topic: str, body_pages: int) -> list[tuple[str, list[str]]]:
    if _is_machine_learning_topic(topic):
        candidates = [
            (
                "为什么需要机器学习",
                [
                    "版式：three_column",
                    "组件：rich_cards",
                    "支撑：规则系统的局限、数据中的规律和学习目标。",
                    "机器学习要解决的是规则难以手写、但数据中确实存在规律的问题。",
                    "规则方法：需要人提前列条件；遇到例外就要补规则；复杂场景维护成本迅速升高",
                    "数据规律：历史样本里包含经验；模型把经验压缩成可复用模式；新样本可用同一模式预测",
                    "学习目标：先分清输入、标签和模型；再理解训练与验证；最后知道它的边界在哪里",
                    "洞察：先问有没有稳定数据闭环，再问模型是否足够复杂。",
                ],
            ),
            (
                "核心思想：从数据中学习规律",
                [
                    "版式：horizontal",
                    "组件：concept_diagram",
                    "支撑：输入、模型、预测和损失四个概念构成学习闭环。",
                    "机器学习的核心不是记忆答案，而是学习能迁移到新样本的映射关系。",
                    "输入 x：图片、文字、表格或传感器记录；需要转成特征；质量决定学习上限",
                    "模型 fθ：把输入映射成预测；参数 θ 会在训练中更新；复杂度要匹配任务难度",
                    "预测 ŷ：模型给出对新样本的估计；可以是类别、数值或排序；需要和真实标签比较",
                    "损失 J：衡量预测与目标的差距；训练让损失变小；验证检查是否只是在背题",
                    "洞察：导论课要先建立词汇表，后面的算法才讲得动。",
                ],
            ),
            (
                "最小例子：房价预测",
                [
                    "版式：horizontal",
                    "组件：example_walkthrough",
                    "支撑：用房屋面积预测价格，把抽象术语落到一个可算例子。",
                    "用房价预测可以串起输入、标签、模型、损失和泛化这五个关键词。",
                    "准备数据：输入是面积、位置和房龄；标签是成交价；先检查缺失值和异常样本",
                    "建立模型：从线性关系开始；预测值写作 ŷ=fθ(x)；参数代表各特征的影响",
                    "公式：J(θ)=1/m ∑ᵢ L(yᵢ, fθ(xᵢ))，损失越小代表整体预测越接近标签",
                    "验证泛化：留出新房源测试；看误差是否稳定；失败样例会提示数据或特征问题",
                ],
            ),
            (
                "三类经典任务",
                [
                    "版式：three_column",
                    "组件：rich_cards",
                    "支撑：用任务目标、典型例子和评价方式区分三类学习。",
                    "不同任务的差别，不在模型名字，而在反馈信号和评价方式。",
                    "监督学习：有标签样本；用于分类和回归；看准确率、召回率或预测误差",
                    "无监督学习：没有标准答案；用于聚类、降维和异常发现；重在帮助探索结构",
                    "强化学习：通过行动获得奖励；用于策略优化；关键是长期收益而非单步正确",
                    "洞察：先识别任务类型，再讨论算法选择。",
                ],
            ),
            (
                "训练流程与验证闭环",
                [
                    "版式：horizontal",
                    "组件：process",
                    "支撑：按数据、训练、验证、迭代四步展开。",
                    "一个可用模型来自反复验证，而不是一次训练完成。",
                    "数据准备：收集样本；清洗噪声；划分训练/验证/测试集",
                    "模型训练：设定目标函数；更新参数 θ；观察损失是否下降",
                    "效果验证：比较测试指标；查看失败案例；确认是否能迁移到新数据",
                    "迭代上线：补充数据；监控漂移；保留人工复核和回滚机制",
                ],
            ),
            (
                "常见误区与下一步",
                [
                    "版式：summary",
                    "组件：summary",
                    "支撑：误区、练习和学习路径共同收束。",
                    "学完导论后，最重要的是带走验证习惯，而不是记住更多名词。",
                    "常见误区：训练集高分不等于真实可靠；相关性不等于因果；大模型不一定适合所有任务",
                    "课堂练习：给一个垃圾邮件分类任务；标出输入、标签、模型输出和评价指标",
                    "继续学习：先跑通小数据实验；记录假设和失败原因；再进入具体算法和深度学习",
                    "洞察：机器学习的第一课，是把问题说清楚、把反馈闭环建起来。",
                ],
            ),
        ]
    else:
        candidates = [
            (
                "学习目标与现实动机",
                [
                    "版式：three_column",
                    "组件：rich_cards",
                    f"支撑：用定义、例子和学习目标展开 {topic}。",
                    f"这一页先回答为什么要学 {topic}，以及学完后能判断什么。",
                    "现实动机：说明它出现在什么场景；解决什么问题；为什么现在值得学习",
                    "学习目标：掌握核心概念；能复述基本流程；能识别常见误区",
                    "课堂例子：选择一个熟悉情境；把抽象概念放进去；用反例说明边界",
                ],
            ),
            (
                "核心概念",
                [
                    "版式：horizontal",
                    "组件：concept_diagram",
                    "支撑：用关键词、关系和边界建立共同语言。",
                    f"学习 {topic} 之前，需要先把几个基础词汇放到同一张地图里。",
                    "关键词一：给出短定义；说明它解决的问题；配一个日常例子",
                    "关键词二：说明它和前一个概念的区别；指出常见混淆；补一个反例",
                    "关键词三：解释它在流程中的作用；说明输入输出；提示后续学习路径",
                    "边界条件：说明什么时候不适用；需要哪些前提；如何检查理解是否正确",
                ],
            ),
            (
                "一个最小案例",
                [
                    "版式：horizontal",
                    "组件：process",
                    "支撑：用最小案例把概念转成可操作步骤。",
                    f"用一个小案例把 {topic} 从定义讲到操作，学生才知道如何使用。",
                    "提出问题：明确对象和目标；说明已有材料；写出判断标准",
                    "拆解步骤：按顺序完成关键动作；记录中间结果；保留可复查信息",
                    "检查结果：对照标准；找出失败点；决定下一轮怎么改",
                ],
            ),
            (
                "类型与对比",
                [
                    "版式：three_column",
                    "组件：rich_cards",
                    "支撑：用三类对象、适用场景和边界展开。",
                    f"理解 {topic} 时，分类不是为了背名词，而是为了选择合适方法。",
                    "类型一：适用什么场景；优势是什么；不适合什么情况",
                    "类型二：解决另一类问题；需要什么前提；常见错误在哪里",
                    "类型三：适合进阶应用；成本或风险是什么；如何验证效果",
                ],
            ),
            (
                "常见误区",
                [
                    "版式：three_column",
                    "组件：rich_cards",
                    "支撑：用误区、原因和修正方法展开。",
                    f"初学 {topic} 时，及时澄清误区能减少后续学习成本。",
                    "误区一：只记结论不看条件；需要补充适用范围；用反例校正",
                    "误区二：把工具当目标；应先明确问题；再选择方法",
                    "误区三：忽视验证；需要设置检查点；让结果可复现",
                ],
            ),
            (
                "课堂小结与练习",
                [
                    "版式：summary",
                    "组件：summary",
                    "支撑：用三句话小结和一个练习收束。",
                    f"最后把 {topic} 收束成可复述、可练习、可继续学习的路径。",
                    "已经掌握：能说清核心概念；能按步骤分析一个小案例；能指出基本边界",
                    "马上练习：选择一个真实小问题；套用本课流程；写下输入、步骤和评价标准",
                    "下一步：阅读一个入门案例；复现实验或流程；记录失败原因和改进想法",
                ],
            ),
        ]
    return candidates[:body_pages]


def _is_machine_learning_topic(topic: str) -> bool:
    return bool(re.search(r"(机器学习|machine learning|\bML\b)", topic, re.IGNORECASE))


def _project_sections(topic: str, body_pages: int) -> list[tuple[str, list[str]]]:
    candidates = [
        (
            "当前结论先说清",
            [
                "版式：three_column",
                "组件：rich_cards",
                "支撑：用目标、进展和决策点展开。",
                f"{topic} 的汇报应先给出结论，让听众知道本次需要判断什么。",
                "目标：本阶段要交付什么；服务哪个对象；验收标准是什么",
                "进展：已经完成哪些关键事项；哪些结果可复用；哪些还在验证",
                "决策点：需要谁拍板；影响范围是什么；最晚什么时候决定",
            ],
        ),
        (
            "进展与里程碑",
            [
                "版式：horizontal",
                "组件：process",
                "支撑：按已完成、进行中、下一步展开。",
                "项目汇报要把状态讲成时间线和责任闭环，而不是散点记录。",
                "已完成：列出可验收成果；标注负责人；说明验证方式",
                "进行中：说明当前卡点；给出预计完成时间；同步依赖方",
                "下一步：拆成具体行动；明确交付物；安排检查节点",
            ],
        ),
        (
            "风险与行动项",
            [
                "版式：table",
                "组件：table",
                "支撑：用风险、影响、责任人和应对动作展开。",
                "风险：影响 / 当前信号 / 应对动作",
                "进度风险：影响交付时间 / 依赖未闭环 / 每周同步阻塞清单",
                "质量风险：影响上线稳定 / 测试覆盖不足 / 补充验证样例",
                "协作风险：影响决策效率 / 需求口径变化 / 固化版本和负责人",
            ],
        ),
    ]
    return (candidates * 3)[:body_pages]


def _research_sections(topic: str, body_pages: int) -> list[tuple[str, list[str]]]:
    candidates = [
        (
            "研究问题与贡献",
            [
                "版式：three_column",
                "组件：rich_cards",
                "支撑：用问题、缺口和贡献展开。",
                f"{topic} 的研究汇报要先说明问题为何重要，以及本工作补上了什么。",
                "问题：研究对象是什么；为什么现有方法不够；关键难点在哪里",
                "缺口：已有工作解决到哪一步；还缺什么验证；为什么现在可以推进",
                "贡献：提出什么方法或发现；带来什么改进；适用边界是什么",
            ],
        ),
        (
            "方法与实验设计",
            [
                "版式：horizontal",
                "组件：process",
                "支撑：按数据、方法、实验和评价展开。",
                "方法页要让别人能复现，而不是只看到模型或公式名。",
                "数据/材料：来源、规模和预处理；说明筛选标准；记录排除条件",
                "方法步骤：说明关键假设；列出主要计算或实验流程；保留参数设置",
                "评价设计：选择对照组；定义指标；检查统计显著性或误差来源",
            ],
        ),
        (
            "结果、局限与下一步",
            [
                "版式：three_column",
                "组件：rich_cards",
                "支撑：用结果、局限和后续实验展开。",
                "好的研究总结要同时讲清发现、可信度和下一步验证。",
                "主要结果：列出最关键发现；说明相对基线提升；指出最强证据",
                "局限性：样本、假设或方法的边界；哪些场景不能外推；可能偏差在哪里",
                "下一步：补充实验；扩大数据或场景；把结论推进到可复现材料",
            ],
        ),
    ]
    return (candidates * 3)[:body_pages]


def _product_sections(topic: str, body_pages: int) -> list[tuple[str, list[str]]]:
    candidates = [
        (
            "用户场景与痛点",
            [
                "版式：three_column",
                "组件：rich_cards",
                "支撑：用用户、任务和痛点展开。",
                f"{topic} 的介绍应从真实使用场景开始，而不是先堆功能。",
                "用户：谁会使用；在什么情境下使用；成功标准是什么",
                "任务：用户要完成什么；当前流程哪里慢；哪些步骤容易出错",
                "痛点：成本、效率或风险在哪里；为什么旧方案不够；影响有多大",
            ],
        ),
        (
            "能力与工作流",
            [
                "版式：horizontal",
                "组件：process",
                "支撑：按输入、处理、输出和反馈展开。",
                "产品能力要讲成工作流，让听众知道它如何进入现有流程。",
                "输入：接收哪些资料；需要什么权限；如何保证质量",
                "处理：核心能力做什么；自动化到哪一步；哪里保留人工确认",
                "输出：交付什么结果；如何下载或协作；如何进入下一步",
                "反馈：用户如何修正；系统如何学习偏好；如何监控质量",
            ],
        ),
        (
            "价值与落地路径",
            [
                "版式：three_column",
                "组件：rich_cards",
                "支撑：用价值、边界和行动项展开。",
                "产品介绍最后要落到可试用、可评估、可推进的行动路径。",
                "核心价值：节省时间；降低重复劳动；提高结果一致性",
                "使用边界：不替代最终判断；需要数据和权限；关键结果要可审阅",
                "下一步：选择试点场景；定义验收指标；安排反馈和迭代节奏",
            ],
        ),
    ]
    return (candidates * 3)[:body_pages]


def _general_sections(topic: str, body_pages: int) -> list[tuple[str, list[str]]]:
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
            "核心概念",
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


def _slide_from_section(section_title: str, raw_items: list[str]) -> Slide:
    layout_hint: Layout | None = None
    visual_hint: str | None = None
    insight: str | None = None
    support: str | None = None
    content_items: list[str] = []

    for item in raw_items:
        layout_match = LAYOUT_LABEL_RE.match(item)
        if layout_match:
            layout_hint = _layout_from_hint(layout_match.group(1)) or layout_hint
            visual_hint = _visual_from_hint(layout_match.group(1)) or visual_hint
            continue

        visual_match = VISUAL_LABEL_RE.match(item)
        if visual_match:
            visual_hint = _visual_from_hint(visual_match.group(1)) or visual_hint
            continue

        insight_match = INSIGHT_LABEL_RE.match(item)
        if insight_match:
            insight = _clip(_clean_inline(insight_match.group(1)), MAX_BULLET_CHARS)
            continue

        support_match = SUPPORT_LABEL_RE.match(item)
        if support_match:
            if support is None:
                support = _clip(_clean_inline(support_match.group(1)), 120)
            else:
                content_items.append(item)
            continue

        content_items.append(item)

    layout = layout_hint or Layout.ONE_COLUMN
    visual = visual_hint or _default_visual_for_layout(layout)
    bullets = [_clip(_clean_content_line(item), MAX_BULLET_CHARS) for item in content_items[:MAX_BULLETS]]
    bullets = [item for item in bullets if item]
    if not bullets:
        bullets = ["请补充这一页的要点。"]

    columns: list[Column] = []
    items: list[HorizontalItem] = []
    table: TableData | None = None

    if visual == "table":
        layout = Layout.TABLE
    elif visual == "two_column":
        layout = Layout.COMPARISON if layout == Layout.COMPARISON else Layout.TWO_COLUMN
    elif visual == "three_column":
        layout = Layout.THREE_COLUMN
    elif visual in {"horizontal", "process", "example_walkthrough", "concept_diagram"} and layout == Layout.ONE_COLUMN:
        layout = Layout.HORIZONTAL
    elif visual == "summary" and layout == Layout.ONE_COLUMN:
        layout = Layout.SUMMARY

    if layout in {Layout.TWO_COLUMN, Layout.COMPARISON}:
        columns = _columns_from_items(bullets, 2)
    elif layout == Layout.THREE_COLUMN:
        columns = _columns_from_items(bullets, 3)
    elif layout in {Layout.HORIZONTAL, Layout.SUMMARY}:
        items = _horizontal_items_from_items(bullets)
    elif layout == Layout.TABLE:
        table = _table_from_items(bullets)

    return Slide(
        layout=layout,
        title=_clip(section_title, MAX_TITLE_CHARS),
        visual=visual,
        proof=support,
        support=support,
        bullets=bullets,
        columns=columns,
        items=items,
        table=table,
        insight=insight,
    )


def _layout_from_hint(value: str) -> Layout | None:
    token = _design_token(value)
    for alias, layout in LAYOUT_ALIASES.items():
        alias_token = _design_token(alias)
        if token == alias_token:
            return layout
    for alias, layout in LAYOUT_ALIASES.items():
        if _design_token(alias) in token:
            return layout
    return None


def _visual_from_hint(value: str) -> str | None:
    token = _design_token(value)
    for alias, visual in VISUAL_ALIASES.items():
        alias_token = _design_token(alias)
        if token == alias_token:
            return visual
    for alias, visual in VISUAL_ALIASES.items():
        if _design_token(alias) in token:
            return visual
    return None


def _design_token(value: str) -> str:
    value = _clean_inline(value).lower()
    return re.sub(r"[\s\-_/]+", "_", value)


def _default_visual_for_layout(layout: Layout) -> str | None:
    if layout in {Layout.TWO_COLUMN, Layout.COMPARISON}:
        return "two_column"
    if layout == Layout.THREE_COLUMN:
        return "three_column"
    if layout == Layout.HORIZONTAL:
        return "horizontal"
    if layout == Layout.TABLE:
        return "table"
    if layout == Layout.SUMMARY:
        return "summary"
    return None


def _columns_from_items(items: list[str], count: int) -> list[Column]:
    keyed = [_split_key_value_line(item) for item in items]
    keyed = [(heading, body) for heading, body in keyed if body]
    if len(keyed) >= count:
        return [
            Column(
                heading=_clip(heading, 60),
                bullets=[_clip(point, MAX_BULLET_CHARS) for point in _split_structured_points(body)[:4]],
            )
            for heading, body in keyed[:count]
        ]

    columns: list[Column] = []
    for idx in range(count):
        chunk = items[idx::count]
        heading = f"要点 {idx + 1}"
        body_items = chunk[:4]
        if chunk:
            heading_candidate, body = _split_key_value_line(chunk[0])
            if body:
                heading = heading_candidate
                body_items = _split_structured_points(body)[:4]
            elif len(chunk[0]) <= 18:
                heading = chunk[0]
                body_items = chunk[1:5] or [chunk[0]]
        columns.append(
            Column(
                heading=_clip(heading, 60),
                bullets=[_clip(item, MAX_BULLET_CHARS) for item in body_items],
            )
        )
    return columns


def _horizontal_items_from_items(items: list[str]) -> list[HorizontalItem]:
    horizontal_items: list[HorizontalItem] = []
    for item in items[:5]:
        heading, body = _split_key_value_line(item)
        if body:
            horizontal_items.append(
                HorizontalItem(heading=_clip(heading, 40), desc=_clip(body, 80))
            )
        else:
            horizontal_items.append(HorizontalItem(heading=_clip(item, 40), desc=""))
    return horizontal_items


def _table_from_items(items: list[str]) -> TableData:
    rows = [_table_cells_from_item(item) for item in items]
    rows = [row for row in rows if len(row) >= 2]
    if len(rows) >= 2:
        headers = _fit_table_row(rows[0])
        data_rows = [_fit_table_row(row, len(headers)) for row in rows[1:6]]
        return TableData(headers=headers, rows=data_rows)

    fallback_rows = [
        [_clip(_split_key_value_line(item)[0], 40), _clip(_split_key_value_line(item)[1] or item, 90)]
        for item in items[:5]
    ]
    return TableData(headers=["项目", "说明"], rows=fallback_rows)


def _table_cells_from_item(item: str) -> list[str]:
    heading, body = _split_key_value_line(item)
    if body:
        return [heading, *_split_table_cells(body)]
    return _split_table_cells(item)


def _split_table_cells(text: str) -> list[str]:
    parts = re.split(r"\s*(?:\||/|；|;)\s*", text)
    return [_clean_inline(part.strip(" 。")) for part in parts if part.strip(" 。")]


def _fit_table_row(row: list[str], width: int | None = None) -> list[str]:
    target_width = min(width or len(row), 4)
    fitted = [_clip(cell, 42) for cell in row[:target_width]]
    while len(fitted) < target_width:
        fitted.append("")
    return fitted


def _split_key_value_line(text: str) -> tuple[str, str]:
    match = re.match(r"^([^：:]{1,24})[：:]\s*(.+)$", text)
    if match:
        return _clean_inline(match.group(1)), _clean_inline(match.group(2))
    return _clip(_clean_inline(text), 28), ""


def _split_structured_points(text: str) -> list[str]:
    text = _clean_inline(text)
    parts = [part.strip(" 。；;") for part in re.split(r"\s*[；;]\s*", text)]
    if len(parts) == 1 and "。" in text:
        parts = [part.strip(" 。") for part in re.split(r"\s*。\s*", text)]
    return [part for part in parts if part] or [text]


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
            current_bullets.append(_clean_content_line(bullet_match.group(1)))
            continue

        if current_title is None:
            if deck_title:
                if not _is_low_value_cover_line(line):
                    cover_notes.append(_clean_inline(line))
                continue
            current_title = "主要内容"
        current_bullets.append(_clean_content_line(line))

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
                _append_unique(bullets, _clean_content_line(cleaned_heading))
            continue
        bullet_match = BULLET_RE.match(line)
        if bullet_match:
            _append_unique(bullets, _clean_content_line(bullet_match.group(1)))
            continue
        table_text = _table_row_text(line)
        if table_text:
            _append_unique(bullets, _clean_content_line(table_text))
            continue
        cleaned = _clean_inline(line.lstrip("> "))
        if cleaned and not _is_low_value_content_line(cleaned):
            _append_unique(bullets, _clean_content_line(cleaned))
    return bullets


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


def _clean_content_line(text: str) -> str:
    return CONTENT_LABEL_RE.sub("", _clean_inline(text)).strip()


def _clip(text: str, max_chars: int) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _chunks(items: list[str], size: int) -> list[list[str]]:
    return [items[idx : idx + size] for idx in range(0, len(items), size)]
