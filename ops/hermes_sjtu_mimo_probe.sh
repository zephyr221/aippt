#!/usr/bin/env bash
set -euo pipefail

HERMES_PROVIDER="${HERMES_PROVIDER:-xiaomi}"
HERMES_MODEL="${HERMES_MODEL:-mimo-v2.5-pro}"
WORK_ROOT="${AIPPT_HERMES_PROBE_ROOT:-/srv/aippt/hermes_probe}"
BUILDER_PY="${AIPPT_BUILDER_PY:-/srv/aippt/venvs/ppt-builder/bin/python}"
SCRIPT_TIMEOUT_SECONDS="${AIPPT_HERMES_SCRIPT_TIMEOUT_SECONDS:-180}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${AIPPT_REPO_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
TEMPLATE_DIR="${AIPPT_SJTU_TEMPLATE_DIR:-$REPO_ROOT/docs/SJTU PPT 模板}"

if ! command -v hermes >/dev/null 2>&1; then
  echo "hermes command not found" >&2
  exit 1
fi

if [ ! -x "$BUILDER_PY" ]; then
  echo "builder python not found or not executable: $BUILDER_PY" >&2
  exit 1
fi

for required in "$TEMPLATE_DIR/SKILL_SJTU.md" "$TEMPLATE_DIR/SJTU 模板.pptx"; do
  if [ ! -f "$required" ]; then
    echo "missing SJTU template asset: $required" >&2
    exit 1
  fi
done

stamp="$(date +%Y%m%d%H%M%S)"
workspace="$WORK_ROOT/sjtu_mimo_$stamp"
mkdir -p "$workspace"/{input,skill,assets,ir,scripts/slides,out,logs,preview}

cp "$TEMPLATE_DIR/SKILL_SJTU.md" "$workspace/skill/SKILL_SJTU.md"
cp "$TEMPLATE_DIR/SJTU 模板.pptx" "$workspace/assets/SJTU 模板.pptx"

brief_arg="${1:-}"
if [ -n "$brief_arg" ]; then
  cp "$brief_arg" "$workspace/input/brief.md"
else
  cat > "$workspace/input/brief.md" <<'BRIEF'
# AIPPT Hermes / MiMo 研发汇报

场景：SJTU 计算材料课程组内部组会。
听众：研究生、青年教师、准备把 AI Agent 用进科研和课件制作的人。
目标：解释为什么 AIPPT 要把 Hermes 作为 agent 核心，为什么 MiMo 适合做 PPT planner/builder，并展示下一步工程路线。
风格：学术组会，克制、清晰、可执行；使用 SJTU Wine Red + Gold 模板。
页数：8-10 页。
BRIEF
fi

cat > "$workspace/AGENTS.md" <<'AGENTS'
# AIPPT Hermes PPT Workspace

You are helping AIPPT make SJTU-style academic presentation decks.

- Plan the claim spine before writing slide code.
- Preserve user and lab preferences through Hermes memory.
- Prefer SJTU Wine Red + Gold visual language.
- Use the files inside this workspace only.
- Do not read secrets, install dependencies, use the network, or call subprocesses.
- For generated PPTX code, write deterministic python-pptx code and save artifacts under `out/`.
AGENTS

brief_text="$(cat "$workspace/input/brief.md")"
style_summary="$(cat <<'STYLE'
- Use SJTU Wine Red + Gold: SJTU_RED #A62038, GOLD #C5A46C, GOLD_PALE #F0E6D2.
- Template layouts: 0 cover, 7 content with red top bar, 12 thanks.
- Content header only fills placeholder idx=11; clear idx=12.
- Avoid Chinese italics, large SJTU_DEEP fills, extra header decoration, footer lines, and traditional Chinese numerals.
- Prefer component pages over pure bullet pages: toc group cards, stat_callout, step_flow, cards, quote_block, chevron_flow, roadmap, insight.
- Keep academic tone: concise, clear, executable, not marketing-heavy.
- Bullet text should be short; each non-cover slide needs a strong claim.
STYLE
)"

spec_prompt="$(cat <<PROMPT
你是 AIPPT 的 Hermes/MiMo PPT architect。请一次性输出组件化 deck spec；它既是故事规划，也是后续 python-pptx runtime 的编译输入。

你必须体现 Hermes 的记忆/学习价值：如何记录用户偏好、课题组习惯、PPT 密度、语气和视觉风格，并让后续 PPT 越做越贴近用户。

硬性要求：
- 只输出 JSON，不要 Markdown 代码围栏，不要解释。
- 顶层字段：title, subtitle, author, story_spine, builder_notes, slides。
- slides 必须为 8-10 页。
- 第一页 type 必须是 cover，最后一页 type 必须是 thanks。
- 允许的 type：cover, toc, stats, flow, cards, quote, chevrons, roadmap, thanks。
- 每个非封面/封底 slide 必须包含 title, claim。
- 不要写 Python 代码。
- bullet 每条不超过 32 个中文字符。
- 至少使用 5 种组件语义：stats, flow, cards, quote, chevrons, roadmap, toc。

JSON schema 草案：
{
  "title": "deck title",
  "subtitle": "deck subtitle",
  "author": "AIPPT Hermes MiMo",
  "story_spine": ["claim 1", "claim 2"],
  "builder_notes": ["spacing note", "memory note"],
  "slides": [
    {"type": "cover", "title": "...", "subtitle": "...", "date": "2026"},
    {"type": "toc", "title": "报告框架", "groups": [{"title": "...", "items": ["..."]}]},
    {"type": "stats", "title": "...", "claim": "...", "stats": [{"number": "3-5", "unit": "h", "label": "...", "desc": "..."}], "insight": "..."},
    {"type": "flow", "title": "...", "claim": "...", "steps": ["...", "..."], "quote": "..."},
    {"type": "cards", "title": "...", "claim": "...", "cards": [{"label": "...", "text": "...", "bullets": ["..."]}], "insight": "..."},
    {"type": "chevrons", "title": "...", "claim": "...", "items": [{"label": "...", "sub": "..."}], "insight": "..."},
    {"type": "roadmap", "title": "...", "claim": "...", "steps": [{"label": "Q1", "text": "..."}], "insight": "..."},
    {"type": "quote", "title": "...", "claim": "...", "quote": "...", "source": "...", "bullets": ["..."]},
    {"type": "thanks", "title": "谢谢"}
  ]
}

SJTU 模板规范摘要：
$style_summary

原始 brief：
$brief_text
PROMPT
)"

HERMES_ACCEPT_HOOKS=1 hermes -z "$spec_prompt" \
  --provider "$HERMES_PROVIDER" \
  --model "$HERMES_MODEL" \
  --toolsets memory \
  > "$workspace/ir/deck_spec.raw.json"

"$BUILDER_PY" - "$workspace/ir/deck_spec.raw.json" "$workspace/ir/deck_spec.json" "$workspace/input/mimo_plan.md" <<'PY'
import json
import re
import sys
from pathlib import Path

raw_path = Path(sys.argv[1])
out_path = Path(sys.argv[2])
plan_path = Path(sys.argv[3])
raw = raw_path.read_text(encoding="utf-8").strip()
raw = re.sub(r"^```(?:json)?\s*", "", raw)
raw = re.sub(r"\s*```$", "", raw)
start = raw.find("{")
end = raw.rfind("}")
if start < 0 or end < start:
    raise SystemExit("MiMo did not return a JSON object")
data = json.loads(raw[start : end + 1])
slides = data.get("slides") or []
if not (8 <= len(slides) <= 10):
    raise SystemExit(f"deck spec must contain 8-10 slides, got {len(slides)}")
if slides[0].get("type") != "cover":
    raise SystemExit("first slide must be cover")
if slides[-1].get("type") != "thanks":
    raise SystemExit("last slide must be thanks")
out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
lines = [f"# {data.get('title', 'AIPPT')}", ""]
if data.get("subtitle"):
    lines += [str(data["subtitle"]), ""]
lines += ["## 故事脊柱", ""]
for item in data.get("story_spine") or []:
    lines.append(f"- {item}")
lines += ["", "## 接触表规划", ""]
for idx, slide in enumerate(slides, start=1):
    claim = slide.get("claim", "")
    lines.append(f"{idx}. {slide.get('title', slide.get('type'))} [{slide.get('type')}]")
    if claim:
        lines.append(f"   - {claim}")
lines += ["", "## Builder 注意事项", ""]
for item in data.get("builder_notes") or []:
    lines.append(f"- {item}")
plan_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
print(out_path)
PY

cat > "$workspace/scripts/sjtu_runtime.py" <<'PY'
from __future__ import annotations

from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

SJTU_RED = RGBColor(0xA6, 0x20, 0x38)
SJTU_DEEP = RGBColor(0x6B, 0x15, 0x25)
GOLD = RGBColor(0xC5, 0xA4, 0x6C)
GOLD_PALE = RGBColor(0xF0, 0xE6, 0xD2)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
WARM_GRAY_1 = RGBColor(0xF5, 0xF4, 0xF2)
WARM_GRAY_2 = RGBColor(0xED, 0xEC, 0xEA)
TEXT_PRIMARY = RGBColor(0x1A, 0x1A, 0x2E)
TEXT_BODY = RGBColor(0x3D, 0x3D, 0x4E)
TEXT_CAPTION = RGBColor(0x6B, 0x72, 0x80)
WARN_AMBER = RGBColor(0xC4, 0x7F, 0x17)
FN = "微软雅黑"
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
MARGIN = Inches(0.9)
CW = SLIDE_W - Inches(1.8)


def _set_ea(run) -> None:
    r_pr = run._r.get_or_add_rPr()
    ea = r_pr.find(qn("a:ea"))
    if ea is None:
        ea = r_pr.makeelement(qn("a:ea"), {})
        r_pr.append(ea)
    ea.set("typeface", FN)


def _text(tf, text: str, size: int = 13, color=TEXT_BODY, bold: bool = False, align=PP_ALIGN.LEFT) -> None:
    tf.clear()
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = FN
    p.alignment = align
    if p.runs:
        _set_ea(p.runs[0])


def _center(tf) -> None:
    try:
        body_pr = tf._txBody.find(qn("a:bodyPr"))
        if body_pr is not None:
            body_pr.set("anchor", "ctr")
    except Exception:
        pass


def load_presentation(workspace: Path) -> Presentation:
    prs = Presentation(str(workspace / "assets" / "SJTU 模板.pptx"))
    while len(prs.slides) > 0:
        rid = prs.slides._sldIdLst[0].get(qn("r:id"))
        prs.part.drop_rel(rid)
        prs.slides._sldIdLst.remove(prs.slides._sldIdLst[0])
    return prs


def add_content_slide(prs: Presentation, title: str, page: int):
    slide = prs.slides.add_slide(prs.slide_layouts[7])
    for ph in slide.placeholders:
        idx = ph.placeholder_format.idx
        if idx == 11:
            ph.text = ""
            run = ph.text_frame.paragraphs[0].add_run()
            run.text = title
            run.font.size = Pt(22)
            run.font.bold = True
            run.font.color.rgb = WHITE
            run.font.name = FN
            _set_ea(run)
        elif idx == 12:
            ph.text = ""
    footer(slide, page)
    return slide


def footer(slide, page: int) -> None:
    box = slide.shapes.add_textbox(SLIDE_W - Inches(1.1), SLIDE_H - Inches(0.39), Inches(0.7), Inches(0.25))
    p = box.text_frame.paragraphs[0]
    r1 = p.add_run()
    r1.text = "◆  "
    r1.font.size = Pt(5)
    r1.font.color.rgb = SJTU_RED
    r1.font.name = FN
    _set_ea(r1)
    r2 = p.add_run()
    r2.text = f"{page:02d}"
    r2.font.size = Pt(11)
    r2.font.color.rgb = TEXT_CAPTION
    r2.font.name = FN
    _set_ea(r2)
    p.alignment = PP_ALIGN.RIGHT


def rect(slide, left, top, width, height, fill, border=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if border:
        shape.line.color.rgb = border
        shape.line.width = Pt(0.75)
    else:
        shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def card(slide, left, top, width, height, fill=WHITE, border=WARM_GRAY_2):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = border
    shape.line.width = Pt(0.5)
    shape.shadow.inherit = False
    shape.adjustments[0] = 0.03
    return shape


def pill(slide, left, top, width, height, text: str, bg=SJTU_RED, fg=WHITE):
    shape = card(slide, left, top, width, height, fill=bg, border=bg)
    _text(shape.text_frame, text, 10, fg, True, PP_ALIGN.CENTER)
    _center(shape.text_frame)
    return shape


def badge(slide, left, top, text: str, size=Inches(0.38), bg=SJTU_RED):
    shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, left, top, size, size)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg
    shape.line.fill.background()
    shape.shadow.inherit = False
    shape.text_frame.margin_left = shape.text_frame.margin_right = 0
    shape.text_frame.margin_top = shape.text_frame.margin_bottom = 0
    _text(shape.text_frame, text, 11, WHITE, True, PP_ALIGN.CENTER)
    _center(shape.text_frame)
    return shape


def insight(slide, left, top, width, text: str, accent=GOLD):
    height = Inches(0.5)
    card(slide, left, top, width, height, fill=WARM_GRAY_1, border=WARM_GRAY_2)
    rect(slide, left, top, Pt(3), height, accent)
    box = slide.shapes.add_textbox(left + Pt(14), top, width - Pt(18), height)
    box.text_frame.margin_top = box.text_frame.margin_bottom = 0
    _text(box.text_frame, "▸  " + text, 11, TEXT_BODY, False)
    _center(box.text_frame)


def stat_callout(slide, left, top, width, item: dict[str, Any], accent=SJTU_RED):
    card(slide, left, top, width, Inches(1.15))
    rect(slide, left, top, width, Pt(3), accent)
    label = slide.shapes.add_textbox(left + Inches(0.18), top + Inches(0.1), width - Inches(0.36), Inches(0.22))
    _text(label.text_frame, str(item.get("label", "")), 10, TEXT_CAPTION)
    number = slide.shapes.add_textbox(left + Inches(0.18), top + Inches(0.34), width - Inches(0.36), Inches(0.48))
    tf = number.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    r1 = p.add_run()
    r1.text = str(item.get("number", ""))
    r1.font.size = Pt(30)
    r1.font.bold = True
    r1.font.color.rgb = accent
    r1.font.name = FN
    _set_ea(r1)
    unit = item.get("unit")
    if unit:
        r2 = p.add_run()
        r2.text = " " + str(unit)
        r2.font.size = Pt(12)
        r2.font.color.rgb = TEXT_CAPTION
        r2.font.name = FN
        _set_ea(r2)
    desc = slide.shapes.add_textbox(left + Inches(0.18), top + Inches(0.82), width - Inches(0.36), Inches(0.22))
    _text(desc.text_frame, str(item.get("desc", "")), 8, TEXT_CAPTION)


def quote_block(slide, left, top, width, text: str, source: str = ""):
    card(slide, left, top, width, Inches(1.35), fill=WARM_GRAY_1)
    rect(slide, left, top, Pt(4), Inches(1.35), GOLD)
    box = slide.shapes.add_textbox(left + Inches(0.45), top + Inches(0.22), width - Inches(0.9), Inches(0.62))
    _text(box.text_frame, text, 15, TEXT_PRIMARY)
    if source:
        src = slide.shapes.add_textbox(left + Inches(0.45), top + Inches(0.92), width - Inches(0.9), Inches(0.25))
        _text(src.text_frame, "—— " + source, 10, TEXT_CAPTION, False, PP_ALIGN.RIGHT)


def render_cover(prs: Presentation, spec: dict[str, Any]):
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    for ph in slide.placeholders:
        idx = ph.placeholder_format.idx
        if idx == 0:
            ph.text = ""
            p = ph.text_frame.paragraphs[0]
            r = p.add_run()
            r.text = str(spec.get("title", "AIPPT"))
            r.font.size = Pt(38)
            r.font.bold = True
            r.font.color.rgb = WHITE
            r.font.name = FN
            _set_ea(r)
            subtitle = str(spec.get("subtitle", ""))
            if subtitle:
                p2 = ph.text_frame.add_paragraph()
                p2.space_before = Pt(20)
                r2 = p2.add_run()
                r2.text = subtitle
                r2.font.size = Pt(19)
                r2.font.color.rgb = WHITE
                r2.font.name = FN
                _set_ea(r2)
        elif idx == 11:
            ph.text = str(spec.get("date", ""))
    return slide


def render_thanks(prs: Presentation, spec: dict[str, Any]):
    slide = prs.slides.add_slide(prs.slide_layouts[12])
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == 11:
            ph.text = str(spec.get("title", "谢谢"))
    return slide


def render_toc(slide, spec: dict[str, Any]) -> None:
    groups = spec.get("groups") or []
    for idx, group in enumerate(groups[:4]):
        col = idx % 2
        row = idx // 2
        left = MARGIN + Inches(col * 5.9)
        top = Inches(1.25) + Inches(row * 2.65)
        color = [SJTU_RED, GOLD, RGBColor(0x8B, 0x5C, 0x3E), TEXT_PRIMARY][idx]
        card(slide, left, top, Inches(5.55), Inches(2.3))
        rect(slide, left, top, Inches(5.55), Pt(3), color)
        pill(slide, left + Inches(0.22), top + Inches(0.18), Inches(1.55), Inches(0.3), str(group.get("title", "")), color)
        for item_idx, item in enumerate((group.get("items") or [])[:4]):
            y = top + Inches(0.65 + item_idx * 0.38)
            badge(slide, left + Inches(0.28), y, str(item_idx + 1), Inches(0.3), color)
            box = slide.shapes.add_textbox(left + Inches(0.72), y, Inches(4.3), Inches(0.28))
            _text(box.text_frame, str(item), 11, TEXT_PRIMARY, True)


def render_stats(slide, spec: dict[str, Any]) -> None:
    stats = spec.get("stats") or []
    count = min(len(stats), 4)
    width = Inches(11.2 / max(count, 1))
    for idx, item in enumerate(stats[:4]):
        stat_callout(slide, MARGIN + idx * width + Inches(0.05), Inches(1.25), width - Inches(0.15), item, [SJTU_RED, GOLD, WARN_AMBER, TEXT_PRIMARY][idx % 4])
    render_bullets(slide, spec.get("bullets") or [], Inches(1.1), Inches(3.0), Inches(11.0), Inches(2.2))


def render_flow(slide, spec: dict[str, Any]) -> None:
    steps = [str(step) for step in (spec.get("steps") or [])][:6]
    if not steps:
        return
    gap = int(CW / len(steps))
    for idx, step in enumerate(steps):
        x = int(MARGIN + gap * idx + gap / 2) - Inches(0.19)
        if idx > 0:
            prev_x = int(MARGIN + gap * (idx - 1) + gap / 2) + Inches(0.19)
            rect(slide, prev_x, Inches(2.25), x - prev_x, Pt(2), SJTU_RED)
        badge(slide, x, Inches(2.05), str(idx + 1))
        box = slide.shapes.add_textbox(x - Inches(0.75), Inches(2.55), Inches(1.9), Inches(0.45))
        _text(box.text_frame, step, 11, TEXT_PRIMARY, True, PP_ALIGN.CENTER)
    if spec.get("quote"):
        quote_block(slide, MARGIN, Inches(4.35), CW, str(spec["quote"]), str(spec.get("source", "")))


def render_cards(slide, spec: dict[str, Any]) -> None:
    cards = (spec.get("cards") or [])[:4]
    for idx, item in enumerate(cards):
        col = idx % 2
        row = idx // 2
        left = MARGIN + Inches(col * 5.9)
        top = Inches(1.25) + Inches(row * 2.25)
        card(slide, left, top, Inches(5.55), Inches(1.9))
        badge(slide, left + Inches(0.22), top + Inches(0.18), str(idx + 1))
        pill(slide, left + Inches(0.72), top + Inches(0.2), Inches(1.7), Inches(0.28), str(item.get("label", "")), GOLD, SJTU_DEEP)
        box = slide.shapes.add_textbox(left + Inches(0.3), top + Inches(0.65), Inches(4.9), Inches(0.95))
        text = str(item.get("text", ""))
        bullets = item.get("bullets") or []
        if bullets:
            text += "\n" + "\n".join("▪ " + str(b) for b in bullets[:3])
        _text(box.text_frame, text, 11, TEXT_BODY)


def render_chevrons(slide, spec: dict[str, Any]) -> None:
    items = (spec.get("items") or [])[:5]
    if not items:
        return
    cell_w = int(CW / len(items)) - Pt(4)
    for idx, item in enumerate(items):
        x = int(MARGIN + int(CW / len(items)) * idx)
        color = [SJTU_RED, GOLD, RGBColor(0x8B, 0x5C, 0x3E), TEXT_PRIMARY, WARN_AMBER][idx % 5]
        shape = slide.shapes.add_shape(MSO_SHAPE.CHEVRON, x, Inches(2.15), cell_w, Inches(0.62))
        shape.fill.solid()
        shape.fill.fore_color.rgb = color
        shape.line.fill.background()
        _text(shape.text_frame, str(item.get("label", "")), 11, WHITE, True, PP_ALIGN.CENTER)
        box = slide.shapes.add_textbox(x + Inches(0.1), Inches(2.9), cell_w - Inches(0.2), Inches(0.55))
        _text(box.text_frame, str(item.get("sub", "")), 9, TEXT_CAPTION, False, PP_ALIGN.CENTER)


def render_roadmap(slide, spec: dict[str, Any]) -> None:
    steps = spec.get("steps") or []
    render_flow(slide, {"steps": [f"{s.get('label', '')}: {s.get('text', '')}" for s in steps]})


def render_bullets(slide, bullets: list[str], left, top, width, height) -> None:
    if not bullets:
        return
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    for idx, item in enumerate(bullets[:6]):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        r1 = p.add_run()
        r1.text = "  ▪  "
        r1.font.size = Pt(13)
        r1.font.color.rgb = SJTU_RED
        r1.font.name = FN
        _set_ea(r1)
        r2 = p.add_run()
        r2.text = str(item)
        r2.font.size = Pt(13)
        r2.font.color.rgb = TEXT_BODY
        r2.font.name = FN
        _set_ea(r2)
        p.space_before = Pt(5)
        p.space_after = Pt(2)
        p.line_spacing = 1.25


def render_slide(prs: Presentation, spec: dict[str, Any], page: int):
    kind = spec.get("type")
    if kind == "cover":
        return render_cover(prs, spec)
    if kind == "thanks":
        return render_thanks(prs, spec)

    slide = add_content_slide(prs, str(spec.get("title", "")), page)
    claim = str(spec.get("claim", ""))
    if claim:
        insight(slide, MARGIN, Inches(1.05), CW, claim, GOLD)
    if kind == "toc":
        render_toc(slide, spec)
    elif kind == "stats":
        render_stats(slide, spec)
    elif kind == "flow":
        render_flow(slide, spec)
    elif kind == "cards":
        render_cards(slide, spec)
    elif kind == "quote":
        quote_block(slide, MARGIN, Inches(2.0), CW, str(spec.get("quote", "")), str(spec.get("source", "")))
        render_bullets(slide, spec.get("bullets") or [], MARGIN, Inches(3.8), CW, Inches(1.8))
    elif kind == "chevrons":
        render_chevrons(slide, spec)
    elif kind == "roadmap":
        render_roadmap(slide, spec)
    else:
        render_cards(slide, spec)
    if spec.get("insight") and kind != "toc":
        insight(slide, MARGIN, Inches(6.08), CW, str(spec["insight"]), SJTU_RED)
    return slide
PY

cat > "$workspace/scripts/write_slide_modules.py" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

workspace = Path(sys.argv[1])
spec = json.loads((workspace / "ir" / "deck_spec.json").read_text(encoding="utf-8"))
slides_dir = workspace / "scripts" / "slides"
slides_dir.mkdir(parents=True, exist_ok=True)
(slides_dir / "__init__.py").write_text("", encoding="utf-8")

for idx, slide in enumerate(spec["slides"], start=1):
    module = slides_dir / f"slide_{idx:02d}.py"
    module.write_text(
        "from sjtu_runtime import render_slide\n\n"
        f"SLIDE = {slide!r}\n\n"
        "def build(prs, page):\n"
        "    return render_slide(prs, SLIDE, page)\n",
        encoding="utf-8",
    )
print(f"wrote {len(spec['slides'])} slide modules")
PY

cat > "$workspace/scripts/assemble_deck.py" <<'PY'
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

from sjtu_runtime import load_presentation

workspace = Path(sys.argv[1]).resolve()
spec = json.loads((workspace / "ir" / "deck_spec.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(workspace / "scripts"))
prs = load_presentation(workspace)

for idx, _slide in enumerate(spec["slides"], start=1):
    module = importlib.import_module(f"slides.slide_{idx:02d}")
    module.build(prs, idx)

out = workspace / "out" / "mimo-sjtu-template.pptx"
out.parent.mkdir(parents=True, exist_ok=True)
prs.save(out)
print(out)
print(f"slides={len(prs.slides)}")
PY

"$BUILDER_PY" "$workspace/scripts/write_slide_modules.py" "$workspace"

if rg -n "subprocess|requests|urllib|socket|httpx|eval\\(|exec\\(|os\\.system|/root|\\.env|authorized_keys" "$workspace/scripts/slides" > "$workspace/logs/script_guard.log"; then
  echo "generated slide modules failed guard check; see $workspace/logs/script_guard.log" >&2
  exit 1
fi

"$BUILDER_PY" -m py_compile "$workspace/scripts/sjtu_runtime.py" "$workspace/scripts/write_slide_modules.py" "$workspace/scripts/assemble_deck.py" "$workspace"/scripts/slides/*.py

(
  cd "$workspace"
  if command -v timeout >/dev/null 2>&1; then
    timeout "$SCRIPT_TIMEOUT_SECONDS" "$BUILDER_PY" scripts/assemble_deck.py "$workspace"
  else
    "$BUILDER_PY" scripts/assemble_deck.py "$workspace"
  fi
) | tee "$workspace/logs/run.log"

"$BUILDER_PY" - "$workspace" <<'PY'
import sys
from pathlib import Path
from pptx import Presentation

workspace = Path(sys.argv[1])
pptx_path = workspace / "out" / "mimo-sjtu-template.pptx"
if not pptx_path.exists() or pptx_path.stat().st_size == 0:
    raise SystemExit(f"missing output: {pptx_path}")
prs = Presentation(pptx_path)
print(f"verified_pptx={pptx_path}")
print(f"slide_count={len(prs.slides)}")
PY

if command -v soffice >/dev/null 2>&1; then
  soffice --headless --convert-to pdf --outdir "$workspace/preview" "$workspace/out/mimo-sjtu-template.pptx" >/dev/null 2>&1 || true
fi

cat > "$workspace/manifest.txt" <<EOF_MANIFEST
workspace=$workspace
brief=$workspace/input/brief.md
plan=$workspace/input/mimo_plan.md
deck_spec=$workspace/ir/deck_spec.json
runtime=$workspace/scripts/sjtu_runtime.py
assembler=$workspace/scripts/assemble_deck.py
slide_modules=$workspace/scripts/slides
pptx=$workspace/out/mimo-sjtu-template.pptx
preview=$workspace/preview
provider=$HERMES_PROVIDER
model=$HERMES_MODEL
EOF_MANIFEST

cat "$workspace/manifest.txt"
