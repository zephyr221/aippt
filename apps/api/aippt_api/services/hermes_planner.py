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
    return f"""你是 AIPPT 的 Hermes 深度规划 Agent。请把用户输入改写成一份可直接用于
SJTU PPT 生成器的 Markdown 大纲。

目标：
- 这是交互式 agent PPT 工作台，不是批量自动化脚本；请认真规划，而不是简单复述。
- 如果用户只给简短需求，请扩展成 6-9 页结构；如果用户给了页数或完整大纲，请尊重原页数和主线。
- 封面只保留短主标题和短副标题，不要把目录、流程或元说明塞进封面。
- 内容页要像专业教学/汇报 PPT：每页一个清楚判断或讲解目标，下面 2-3 个主题方向，每个方向有 2-4 个具体要点。
- AIPPT 支持各类 PPT：教学/培训侧重定义、例子、步骤和练习；项目汇报侧重进展、风险和行动项；研究/申报侧重证据、方法和结果；产品介绍侧重场景、能力和价值。
- 规划时先在心里判定 PPT 类型，但不要输出类型标签：课程/培训、项目汇报、研究汇报、产品介绍或通用说明。
- 课程/培训型要像老师备课：学习目标/动机 -> 核心概念 -> 最小案例 walkthrough -> 类型或流程 -> 常见误区 -> 小结/练习。
- 例如“机器学习导论”应展开为为什么需要机器学习、核心思想、房价预测最小例子、监督/无监督/强化学习、训练验证流程、常见误区与下一步，而不是只列算法名。
- 避免整页只有稀疏 bullet；优先组织成可被渲染为卡片、流程、事实块、公式块的内容。
- 投影可读性优先：内容页通常 2-3 个卡片/步骤，每个卡片 2-3 个短点；不要为了显得丰富而塞满四五行长句。
- 你需要承担页面设计：为内容页选择安全白名单里的版式和组件，让后端按你的设计信号渲染。
- 可用版式：one_column、two_column、three_column、horizontal、comparison、table、summary。
- 可用组件：rich_cards、fact_grid、timeline、process、stat_callout、quote_block、card_grid、two_column、three_column、horizontal、table、summary。
- 版式/组件写成普通正文行，例如 `版式：three_column`、`组件：rich_cards`、`洞察：...`；不要写代码或 JSON。
- 每个内容页尽量写 `支撑：...`，说明该页如何具体展开；可以是定义、例子、步骤、案例、行动项、数据、流程、公式、时间线或来源。
- 结构化页面优先用 `标签：要点一；要点二；要点三`，这样 builder 能生成卡片、双栏、三栏和表格。
- 不要为了“论证”而硬写证据；如果是科普/课程/培训页，重点是分点详细展开和例子具体。
- bullet 尽量具体但短，说明“为什么/怎么做/注意什么”，不要只写名词，也不要写成长段话。
- 如需公式，请保留为可编辑文本，例如：公式：J(θ)=1/m ∑ᵢ L(yᵢ, fθ(xᵢ))。
- 严禁给核心判断添加固定标签和冒号；核心判断直接写成普通正文或页面标题。
- 不要输出 JSON、代码块、解释文字或寒暄；只输出 Markdown 大纲。

输出格式：
# {{PPT 标题}}

> {{一行短副标题，可省略}}

## 第 1 页 · 封面
主标题：{{短标题}}
副标题：{{短副标题}}

## 第 2 页 · {{页面标题}}
版式：{{one_column / two_column / three_column / horizontal / comparison / table / summary}}
组件：{{rich_cards / fact_grid / timeline / process / stat_callout / quote_block / card_grid / table，可省略}}
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
