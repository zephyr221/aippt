import os
import re
import shlex
import subprocess
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

    prompt_path = workspace / "input" / "hermes_plan_prompt.md"
    prompt = _planning_prompt(deck, original_outline)
    prompt_path.write_text(prompt, encoding="utf-8")

    command = _hermes_command(settings, prompt)
    env = os.environ.copy()
    env["HERMES_ACCEPT_HOOKS"] = "1"

    result = subprocess.run(
        command,
        cwd=workspace,
        env=env,
        capture_output=True,
        text=True,
        timeout=settings.hermes_plan_timeout_seconds,
        check=False,
    )

    if result.stderr.strip():
        _append_log(workspace, result.stderr.strip())

    raw_path = workspace / "logs" / "hermes_plan.raw.md"
    raw_path.write_text(result.stdout.strip() + "\n", encoding="utf-8")

    if result.returncode != 0:
        provider = settings.hermes_provider or "default"
        model = settings.hermes_model or "default"
        raise RuntimeError(
            f"Hermes planning failed ({result.returncode}) with provider={provider}, model={model}."
        )

    planned_outline = _clean_markdown(result.stdout)
    if len(planned_outline) < 120:
        raise RuntimeError("Hermes planning returned too little content.")

    planned_outline_path = workspace / "ir" / "planned_outline.md"
    planned_outline_path.write_text(planned_outline + "\n", encoding="utf-8")

    report_path = workspace / "logs" / "hermes_plan.md"
    report_path.write_text(_render_report(settings, deck, planned_outline), encoding="utf-8")

    _append_log(workspace, "Hermes deep planning wrote ir/planned_outline.md")
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


def _planning_prompt(deck: DeckSession, original_outline: str) -> str:
    return f"""你是 AIPPT 的 Hermes 深度规划 Agent。请把用户输入改写成一份可直接用于
SJTU PPT 生成器的 Markdown 大纲。

目标：
- 这是交互式 agent PPT 工作台，不是批量自动化脚本；请认真规划，而不是简单复述。
- 如果用户只给一句话需求，请扩展成 5-8 页结构；如果用户给了页数或完整大纲，请尊重原页数和主线。
- 封面只保留短主标题和短副标题，不要把目录、流程或元说明塞进封面。
- 内容页要像专业教学/汇报 PPT：每页一个核心判断，下面 2-3 个主题方向，每个方向有 2-4 个具体要点。
- 避免整页只有稀疏 bullet；优先组织成可被渲染为卡片、流程、事实块、公式块的内容。
- bullet 尽量具体，说明“为什么/怎么做/注意什么”，不要只写名词。
- 如需公式，请保留为可编辑文本，例如：公式：J(θ)=1/m ∑ᵢ L(yᵢ, fθ(xᵢ))。
- 不要输出 JSON、代码块、解释文字或寒暄；只输出 Markdown 大纲。

输出格式：
# {{PPT 标题}}

> {{一行短副标题，可省略}}

## 第 1 页 · 封面
主标题：{{短标题}}
副标题：{{短副标题}}

## 第 2 页 · {{页面标题}}
一句话：{{本页核心判断}}
- {{主题一}}：{{2-3 句具体展开}}
- {{主题二}}：{{2-3 句具体展开}}
- {{主题三}}：{{2-3 句具体展开，可省略}}

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
    return "\n".join(lines)


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
