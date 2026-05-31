import codecs
import os
import re
import shlex
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..config import Settings
from ..models import DeckSession


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


@dataclass(frozen=True)
class PlanningArtifact:
    outline_path: Path
    report_path: Path
    raw_path: Path


def write_hermes_plan(settings: Settings, deck: DeckSession, workspace: Path) -> PlanningArtifact:
    """Run the interactive Hermes planner and persist its Markdown outline."""
    if not settings.hermes_planner_enabled:
        raise RuntimeError("Hermes deep planning is not enabled on this server.")

    outline_path = workspace / "input" / "outline.md"
    original_outline = outline_path.read_text(encoding="utf-8") if outline_path.is_file() else ""
    if not original_outline.strip():
        raise RuntimeError("Cannot run Hermes planning without an input brief or outline.")

    _append_agent_log(workspace, f"识别需求：{_brief_summary(original_outline)}")
    _append_agent_log(workspace, f"规划策略：{_planning_strategy(original_outline)}")
    _append_agent_log(workspace, "准备调用 Hermes/MiMo 生成页面结构和讲述顺序。")

    prompt_path = workspace / "input" / "hermes_plan_prompt.md"
    prompt = _planning_prompt(deck, original_outline)
    prompt_path.write_text(prompt, encoding="utf-8")

    command = _hermes_command(settings, prompt)
    env = os.environ.copy()
    env["HERMES_ACCEPT_HOOKS"] = "1"

    _append_agent_log(workspace, "Hermes/MiMo 正在规划：压缩标题、组织卡片、检查公式与边界表达。")
    returncode, stdout, stderr = _run_hermes_command(
        command=command,
        workspace=workspace,
        env=env,
        timeout_seconds=settings.hermes_plan_timeout_seconds,
    )

    raw_path = workspace / "logs" / "hermes_plan.raw.md"
    if not raw_path.exists():
        raw_path.write_text(stdout.strip() + "\n", encoding="utf-8")
    if stderr.strip():
        _append_log(workspace, stderr.strip())

    if returncode != 0:
        provider = settings.hermes_provider or "default"
        model = settings.hermes_model or "default"
        raise RuntimeError(
            f"Hermes planning failed ({returncode}) with provider={provider}, model={model}."
        )

    planned_outline = _clean_markdown(stdout)
    if len(planned_outline) < 120:
        raise RuntimeError("Hermes planning returned too little content.")
    planned_outline = _normalize_requested_page_count(planned_outline, original_outline, workspace)

    planned_outline_path = workspace / "ir" / "planned_outline.md"
    planned_outline_path.write_text(planned_outline + "\n", encoding="utf-8")

    report_path = workspace / "logs" / "hermes_plan.md"
    report_path.write_text(_render_report(settings, deck, planned_outline), encoding="utf-8")

    _append_agent_log(workspace, f"完成规划：{_outline_summary(planned_outline)}")
    _append_agent_log(workspace, "已写入规划大纲，准备进入 PPTX 渲染。")
    return PlanningArtifact(
        outline_path=planned_outline_path,
        report_path=report_path,
        raw_path=raw_path,
    )


def _hermes_command(settings: Settings, prompt: str) -> list[str]:
    command = [*shlex.split(settings.hermes_command), "-z", prompt]
    if settings.hermes_provider:
        command.extend(["--provider", settings.hermes_provider])
    if settings.hermes_model:
        command.extend(["--model", settings.hermes_model])
    if settings.hermes_toolsets:
        command.extend(["--toolsets", settings.hermes_toolsets])
    if settings.hermes_skills:
        command.extend(["--skills", settings.hermes_skills])
    return command


def _run_hermes_command(
    *,
    command: list[str],
    workspace: Path,
    env: dict[str, str],
    timeout_seconds: int,
) -> tuple[int, str, str]:
    raw_path = workspace / "logs" / "hermes_plan.raw.md"
    process = subprocess.Popen(
        command,
        cwd=workspace,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
    )
    if process.stdout is None or process.stderr is None:
        raise RuntimeError("Hermes command did not expose stdout/stderr pipes.")

    stdout_fd = process.stdout.fileno()
    stderr_fd = process.stderr.fileno()
    os.set_blocking(stdout_fd, False)
    os.set_blocking(stderr_fd, False)
    stdout_decoder = codecs.getincrementaldecoder("utf-8")("replace")
    stderr_decoder = codecs.getincrementaldecoder("utf-8")("replace")
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    stdout_buffer = ""
    seen: set[str] = set()
    deadline = time.monotonic() + timeout_seconds
    next_heartbeat = time.monotonic() + 25

    with raw_path.open("w", encoding="utf-8") as raw:
        open_fds = {stdout_fd, stderr_fd}
        while open_fds:
            now = time.monotonic()
            if now >= deadline:
                process.kill()
                process.wait()
                raise RuntimeError(f"Hermes planning timed out after {timeout_seconds} seconds.")

            for fd, decoder, chunks in (
                (stdout_fd, stdout_decoder, stdout_chunks),
                (stderr_fd, stderr_decoder, stderr_chunks),
            ):
                if fd not in open_fds:
                    continue
                try:
                    data = os.read(fd, 4096)
                except BlockingIOError:
                    continue
                if not data:
                    open_fds.remove(fd)
                    tail = decoder.decode(b"", final=True)
                    if tail:
                        chunks.append(tail)
                        if fd == stdout_fd:
                            raw.write(tail)
                            raw.flush()
                            stdout_buffer = _emit_outline_progress(workspace, stdout_buffer + tail, seen)
                    continue

                text = decoder.decode(data)
                chunks.append(text)
                if fd == stdout_fd:
                    raw.write(text)
                    raw.flush()
                    stdout_buffer = _emit_outline_progress(workspace, stdout_buffer + text, seen)

            if time.monotonic() >= next_heartbeat and process.poll() is None:
                _append_agent_log(workspace, "仍在规划：正在检查页面密度、标题长度和卡片结构。")
                next_heartbeat += 25
            time.sleep(0.05)

    if stdout_buffer.strip():
        _maybe_log_outline_line(workspace, stdout_buffer.strip(), seen)
    return process.wait(), "".join(stdout_chunks), "".join(stderr_chunks)


def _planning_prompt(deck: DeckSession, original_outline: str) -> str:
    requested_pages = _requested_total_pages(original_outline)
    if requested_pages:
        outline_pages = max(2, requested_pages - 1)
        page_contract = (
            f"用户明确要求 {requested_pages} 页 PPT，最终 PPTX 必须是 {requested_pages} 页。"
            f"因为系统会自动追加结束页，你输出的 Markdown 必须正好包含 {outline_pages} 个 `## 第 N 页` 页面标题："
            "第 1 页为封面，其余为内容页；不要少页、不要多页。"
        )
    else:
        page_contract = "如果用户未给页数，请规划 6-9 页最终 PPTX；系统会自动追加结束页。"
    return f"""你是 AIPPT 的 Hermes 深度规划 Agent。请把用户输入改写成一份可直接用于
SJTU PPT 生成器的 Markdown 大纲。

目标：
- 这是交互式 agent PPT 工作台，不是批量自动化脚本；请认真规划，而不是简单复述。
- {page_contract}
- 如果用户给了完整大纲，请尊重原页数和主线，不要擅自压缩为更短的默认结构。
- 封面只保留短主标题和短副标题，不要把目录、流程或元说明塞进封面。
- 内容页要像专业教学/汇报 PPT：每页一个清楚判断或讲解目标，下面 2-3 个主题方向，每个方向有 2-4 个具体要点。
- AIPPT 支持各类 PPT：教学/培训侧重定义、例子、步骤和练习；项目汇报侧重进展、风险和行动项；研究/申报侧重证据、方法和结果；产品介绍侧重场景、能力和价值。
- 规划时先在心里判定 PPT 类型，但不要输出类型标签：课程/培训、项目汇报、研究汇报、产品介绍或通用说明。
- 课程/培训型要像老师备课：学习目标/动机 -> 核心概念 -> 最小案例 walkthrough -> 类型/范式 -> 流程闭环 -> 评估或误区 -> 小结/下一步；核心概念页优先用 `组件：concept_diagram`，最小案例页优先用 `组件：example_walkthrough`。
- 例如“机器学习导论”应展开为为什么需要机器学习、核心思想、房价预测最小例子、四类学习范式、训练验证闭环、经典算法速览、模型评估指标、常见误区与下一步，而不是只列算法名。
- 机器学习或 AI 教学页要主动使用更丰富的办公模板节奏：四类学习范式用 `组件：learning_modes`，训练/验证闭环用 `组件：loop_flow`，算法速览用 `组件：numbered_cards`，评估指标或过拟合对比用 `组件：compare_matrix`。
- 导论型课程时间有限，除非用户明确要求，不要硬塞练习页或检查理解页；更重要的是选一条主例子贯穿始终，例如机器学习导论用房价预测串起输入、模型、预测、损失、任务类型和验证闭环。
- 汇报/产品类 PPT 不要全做卡片：总览页优先用 `metric_strip`，阶段进展用 `milestone_timeline`，代表项目用 `project_showcase`，平台/系统介绍用 `media_explain`。
- 避免整页只有稀疏 bullet；优先组织成可被渲染为卡片、流程、事实块、公式块、数字卡、四象限和对比矩阵的内容。
- 避免连续三页使用同一种卡片样式；穿插 `concept_diagram`、`example_walkthrough`、`learning_modes`、`loop_flow`、`numbered_cards`、`compare_matrix`、`summary`，让页面节奏像成熟办公模板而不是同一组件复制。
- 投影可读性优先：内容页通常 2-3 个卡片/步骤，每个卡片 2-3 个短点；不要为了显得丰富而塞满四五行长句。
- 卡片标题要短，中文优先；不要把 `监督学习（Supervised Learning）` 这类中英长标题塞进卡片标题，英文术语可以放入第一条短要点。
- 小卡片每格最多 2 条短要点，每条尽量 18-28 个中文字符；宁可少露一点，也不要让文字溢出边框。
- 你需要承担页面设计：为内容页选择安全白名单里的版式和组件，让后端按你的设计信号渲染。
- 可用版式：one_column、two_column、three_column、horizontal、comparison、table、summary。
- 可用组件：rich_cards、fact_grid、timeline、process、loop_flow、concept_diagram、example_walkthrough、learning_modes、numbered_cards、compare_matrix、metric_strip、milestone_timeline、project_showcase、media_explain、stat_callout、quote_block、card_grid、two_column、three_column、horizontal、table、summary。
- 版式/组件写成普通正文行，例如 `版式：three_column`、`组件：rich_cards`、`洞察：...`；不要写代码或 JSON。
- 每个内容页尽量写 `支撑：...`，说明该页如何具体展开；可以是定义、例子、步骤、案例、行动项、数据、流程、公式、时间线或来源。
- `洞察：...` 不只是总结，也可以承担转场：说明为什么下一页自然要讲这个。
- 结构化页面优先用 `标签：要点一；要点二；要点三`，这样 builder 能生成卡片、双栏、三栏和表格。
- 不要为了“论证”而硬写证据；如果是科普/课程/培训页，重点是分点详细展开和例子具体。
- bullet 尽量具体但短，说明“为什么/怎么做/注意什么”，不要只写名词，也不要写成长段话。
- 如需公式，请保留为可编辑文本，例如：公式：J(θ)=1/m ∑ᵢ L(yᵢ, fθ(xᵢ))。
- 严禁给核心判断添加固定标签和冒号；核心判断直接写成普通正文或页面标题。
- 不要输出 JSON、代码块、解释文字或寒暄；只输出 Markdown 大纲。
- 不要在结尾输出 "Here is the complete outline"、"That's the complete..." 这类英文完成说明。

输出格式：
# {{PPT 标题}}

> {{一行短副标题，可省略}}

## 第 1 页 · 封面
主标题：{{短标题}}
副标题：{{短副标题}}

## 第 2 页 · {{页面标题}}
版式：{{one_column / two_column / three_column / horizontal / comparison / table / summary}}
组件：{{rich_cards / fact_grid / timeline / process / loop_flow / concept_diagram / example_walkthrough / learning_modes / numbered_cards / compare_matrix / metric_strip / milestone_timeline / project_showcase / media_explain / stat_callout / quote_block / card_grid / table，可省略}}
支撑：{{定义、例子、步骤、案例、行动项、数据、流程、公式、时间线或来源；可省略但建议保留}}
{{本页核心判断，直接写内容，不加标签}}
- {{主题一}}：{{2-3 句具体展开}}
- {{主题二}}：{{2-3 句具体展开}}
- {{主题三}}：{{2-3 句具体展开，可省略}}
洞察：{{底部一句可选总结，可省略}}

请确保最后一页不要写“谢谢”，系统会自动添加结束页。

Deck 标题：{deck.title}

用户输入：
{original_outline}
"""


def _clean_markdown(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"^```(?:markdown|md)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(_strip_disallowed_labels(line) for line in lines)


def _normalize_requested_page_count(markdown: str, original_outline: str, workspace: Path) -> str:
    requested_pages = _requested_total_pages(original_outline)
    if not requested_pages:
        return markdown

    expected_headings = max(2, requested_pages - 1)
    heading_count = _outline_page_heading_count(markdown)
    if heading_count == expected_headings:
        return markdown

    if heading_count > expected_headings:
        _append_agent_log(
            workspace,
            f"页数校验：用户要求 {requested_pages} 页，规划偏多，已裁剪为目标页数。",
        )
        return _trim_outline_page_headings(markdown, expected_headings)

    _append_agent_log(
        workspace,
        f"页数校验：用户要求 {requested_pages} 页，规划偏少，已补足到目标页数。",
    )
    return _extend_outline_page_headings(markdown, original_outline, expected_headings, heading_count)


def _outline_page_heading_count(markdown: str) -> int:
    return len(re.findall(r"^##\s*第\s*\d+\s*页", markdown, flags=re.MULTILINE))


def _trim_outline_page_headings(markdown: str, expected_headings: int) -> str:
    lines = markdown.splitlines()
    seen = 0
    keep: list[str] = []
    for line in lines:
        if re.match(r"^##\s*第\s*\d+\s*页", line):
            seen += 1
            if seen > expected_headings:
                break
        keep.append(line)
    return "\n".join(keep).rstrip()


def _extend_outline_page_headings(
    markdown: str,
    original_outline: str,
    expected_headings: int,
    current_headings: int,
) -> str:
    topic = _topic_from_request(original_outline)
    additions: list[str] = []
    templates = [
        (
            "关键概念再澄清",
            "three_column",
            "rich_cards",
            "用定义、反例和边界把概念讲得更稳。",
            ["核心概念：补充一个容易混淆的关键词；说明它和相近概念的区别；给出直观例子", "反例边界：说明什么时候不能这样理解；指出常见误用；给出判断标准", "课堂提示：把这一页和前后页串起来；保留一个可讨论问题"],
        ),
        (
            "应用场景与例子",
            "horizontal",
            "numbered_cards",
            "用三个场景把抽象知识落到真实问题。",
            ["场景一：说明输入材料是什么；目标是什么；结果如何判断", "场景二：解释为什么适合这个方法；需要哪些前提；可能遇到什么限制", "场景三：给出可迁移的观察；连接到课程或汇报主线"],
        ),
        (
            "方法流程拆解",
            "horizontal",
            "loop_flow",
            "按准备、执行、验证和迭代形成闭环。",
            ["准备：明确问题和材料；列出约束；设定评价标准", "执行：按步骤完成核心动作；记录中间结果；避免跳过检查点", "验证：用新样例或反例测试；观察失败原因；决定下一轮改进"],
        ),
        (
            "对比矩阵与判断标准",
            "horizontal",
            "compare_matrix",
            "用对比维度说明什么时候该选哪种方法。",
            ["适用场景：说明最匹配的问题；列出必要前提；指出不适用边界", "评价指标：说明如何判断好坏；连接真实风险；保留验证方式", "取舍建议：给出选择顺序；说明成本；提示下一步动作"],
        ),
        (
            "常见误区与检查",
            "summary",
            "summary",
            "把容易误解的地方收束成检查清单。",
            ["误区一：只记名词不看条件；需要补充适用范围；用反例校正", "误区二：忽视验证；需要设置检查点；让结果可复现", "检查问题：能否用自己的例子复述；能否指出一个边界；能否说明下一步"],
        ),
    ]
    next_page = current_headings + 1
    while next_page <= expected_headings:
        title, layout, component, support, bullets = templates[(next_page - current_headings - 1) % len(templates)]
        additions.extend(
            [
                "",
                f"## 第 {next_page} 页 · {title}",
                f"版式：{layout}",
                f"组件：{component}",
                f"支撑：{support}",
                f"围绕 {topic} 补充一个必要视角，让整套 PPT 的页数和讲述节奏更完整。",
                *[f"- {bullet}" for bullet in bullets],
                f"洞察：这一页用于补齐 {topic} 的理解链条，并自然过渡到后续内容。",
            ]
        )
        next_page += 1
    return (markdown.rstrip() + "\n" + "\n".join(additions).strip()).rstrip()


def _requested_total_pages(text: str) -> int | None:
    digit_range = re.search(r"(\d{1,2})\s*(?:[-~到至]|—)\s*(\d{1,2})\s*页", text)
    if digit_range:
        return _clamp_page_count(int(digit_range.group(2)))
    digit_single = re.search(r"(\d{1,2})\s*页", text)
    if digit_single:
        return _clamp_page_count(int(digit_single.group(1)))
    zh_range = re.search(
        r"([一二两三四五六七八九十]{1,3})\s*(?:到|至|[-~—])\s*"
        r"([一二两三四五六七八九十]{1,3})\s*页",
        text,
    )
    if zh_range:
        return _clamp_page_count(_chinese_number(zh_range.group(2)) or 6)
    zh_pair = re.search(r"([一二两三四五六七八九])([一二两三四五六七八九])\s*页", text)
    if zh_pair:
        return _clamp_page_count(CHINESE_NUMBERS[zh_pair.group(2)])
    zh_single = re.search(r"([一二两三四五六七八九十]{1,3})\s*页", text)
    if zh_single:
        return _clamp_page_count(_chinese_number(zh_single.group(1)) or 6)
    return None


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


def _topic_from_request(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    match = re.search(r"关于\s*(.+?)(?:的)?(?:科普|介绍|分享|报告|PPT|ppt|幻灯片|$)", compact)
    if match:
        return _trim_request_topic(match.group(1)) or "主题"
    compact = re.sub(r"\d{1,2}\s*(?:[-~到至]|—)?\s*\d{0,2}\s*页", " ", compact)
    compact = re.sub(r"(请|帮我|制作|生成|做|写|一份|PPT|ppt|幻灯片|关于|科普|介绍|分享|报告)", " ", compact)
    compact = re.sub(r"[，,。.!！?？:：；;、]+", " ", compact)
    compact = re.sub(r"\s+", " ", compact).strip()
    return _trim_request_topic(compact)[:30] or "主题"


def _trim_request_topic(topic: str) -> str:
    topic = re.split(
        r"[，,。.!！?？:：；;、]\s*(?:其中|重点|主要|尤其|希望|要求|请|并|要|讲)",
        topic,
        maxsplit=1,
    )[0]
    topic = re.split(
        r"\s+(?:其中|重点|主要|尤其|希望|要求|并且|要|重点讲|讲讲|讲一下)\s*",
        topic,
        maxsplit=1,
    )[0]
    return re.sub(r"\s+", " ", topic).strip(" ，,。")


def _emit_outline_progress(workspace: Path, text: str, seen: set[str]) -> str:
    lines = text.split("\n")
    for line in lines[:-1]:
        _maybe_log_outline_line(workspace, line, seen)
    return lines[-1]


def _maybe_log_outline_line(workspace: Path, line: str, seen: set[str]) -> None:
    clean = line.strip()
    if clean.startswith("# "):
        title = clean.lstrip("#").strip()
        key = f"title:{title}"
        if title and key not in seen:
            seen.add(key)
            _append_agent_log(workspace, f"确定主题：{title}")
        return

    if not clean.startswith("## "):
        return

    heading = clean.lstrip("#").strip()
    heading = re.sub(r"^第\s*\d+\s*页\s*[·:：\-—]\s*", "", heading)
    if not heading or heading == "封面":
        return
    key = f"heading:{heading}"
    if key in seen:
        return
    seen.add(key)
    _append_agent_log(workspace, f"正在规划页面：{heading}")


def _strip_disallowed_labels(line: str) -> str:
    return re.sub(r"^(\s*(?:[-*+]\s+|\d+[.)]\s+)?)一句话\s*[：:]\s*", r"\1", line)


def _brief_summary(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact[:80] + ("..." if len(compact) > 80 else "")


def _planning_strategy(text: str) -> str:
    page_count = "尊重用户给定页数" if re.search(r"\d+\s*[-~到至]?\s*\d*\s*页|[一二两三四五六七八九十]+\s*页", text) else "自动规划 5-8 页"
    detail = "按已有大纲重组" if "第 " in text or "##" in text else "从简短需求扩展为教学型大纲"
    return f"{page_count}，{detail}，使用 SJTU 模板卡片化表达。"


def _outline_summary(markdown: str) -> str:
    headings = [
        re.sub(r"^第\s*\d+\s*页\s*[·:：\-—]\s*", "", line.strip("# "))
        for line in markdown.splitlines()
        if line.startswith("## ")
    ]
    headings = [heading for heading in headings if heading and heading != "封面"]
    if not headings:
        return f"生成 {len(markdown)} 字 Markdown 大纲。"
    return " / ".join(headings[:5])


def _render_report(settings: Settings, deck: DeckSession, planned_outline: str) -> str:
    provider = settings.hermes_provider or "(default)"
    model = settings.hermes_model or "(default)"
    lines = [
        "# Hermes Deep Planning",
        "",
        f"- Deck: {deck.title}",
        f"- Provider: {provider}",
        f"- Model: {model}",
        f"- Skills: {settings.hermes_skills or '(none)'}",
        f"- Generated at: {datetime.now(timezone.utc).isoformat()}",
        "- Mode: explicit interactive agent planning",
        "",
        "## Planned Outline",
        "",
        planned_outline,
        "",
    ]
    return "\n".join(lines)


def _append_log(workspace: Path, line: str) -> None:
    log_path = workspace / "logs" / "job.log"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line.rstrip() + "\n")


def _append_agent_log(workspace: Path, line: str) -> None:
    _append_log(workspace, f"AIPPT_AGENT: {line}")
