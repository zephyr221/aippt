import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlmodel import Session, select

from ..config import Settings
from ..models import DeckSession, FileAsset, FileKind
from .preview import PreviewArtifacts, build_preview_artifacts


@dataclass(frozen=True)
class ReviewArtifact:
    report_path: Path
    qa_path: Path
    preview_path: Path | None
    preview_content_type: str | None


def write_hermes_review(
    settings: Settings,
    session: Session,
    deck: DeckSession,
    workspace: Path,
) -> ReviewArtifact:
    """Write a deterministic Hermes-ready review report for the current deck.

    This is intentionally non-destructive. It gives Hermes and humans a stable
    report surface before we allow model-generated repairs into the worker loop.
    """
    outline_path = workspace / "input" / "outline.md"
    deck_ir_asset = _latest_asset(session, deck, FileKind.DECK_IR)
    pptx_asset = _latest_asset(session, deck, FileKind.PPTX)
    pptx_path = Path(pptx_asset.storage_path) if pptx_asset else None

    deck_payload = _read_json_asset(deck_ir_asset)
    preview = build_preview_artifacts(settings, pptx_path, workspace)
    qa = _build_qa(deck, outline_path, deck_payload, deck_ir_asset, pptx_asset, preview, workspace)

    qa_path = workspace / "qa" / "qa.json"
    qa_path.parent.mkdir(parents=True, exist_ok=True)
    qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report_path = workspace / "logs" / "hermes_review.md"
    report_path.write_text(_render_report(deck, qa), encoding="utf-8")
    preview_download = preview.best_download()
    return ReviewArtifact(
        report_path=report_path,
        qa_path=qa_path,
        preview_path=preview_download[0] if preview_download else None,
        preview_content_type=preview_download[1] if preview_download else None,
    )


def _latest_asset(session: Session, deck: DeckSession, kind: FileKind) -> FileAsset | None:
    return session.exec(
        select(FileAsset)
        .where(
            FileAsset.deck_session_id == deck.id,
            FileAsset.owner_user_id == deck.owner_user_id,
            FileAsset.kind == kind,
        )
        .order_by(FileAsset.created_at.desc())
    ).first()


def _read_json_asset(asset: FileAsset | None) -> dict[str, Any] | None:
    if asset is None:
        return None
    path = Path(asset.storage_path)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _build_qa(
    deck: DeckSession,
    outline_path: Path,
    deck_payload: dict[str, Any] | None,
    deck_ir_asset: FileAsset | None,
    pptx_asset: FileAsset | None,
    preview: PreviewArtifacts,
    workspace: Path,
) -> dict[str, Any]:
    slides = _slides(deck_payload)
    issues: list[dict[str, str]] = []
    suggestions: list[str] = []

    if not outline_path.is_file() or not outline_path.read_text(encoding="utf-8").strip():
        issues.append(_issue("high", "input", "缺少可审阅的大纲输入。"))

    if deck_ir_asset is None:
        issues.append(_issue("high", "artifact", "尚未找到 Deck IR，建议先生成 PPTX。"))
    elif deck_payload is None:
        issues.append(_issue("high", "artifact", "Deck IR 无法解析为 JSON。"))

    if pptx_asset is None or not Path(pptx_asset.storage_path).is_file():
        issues.append(_issue("medium", "artifact", "尚未找到可审阅的 PPTX 产物。"))
    elif Path(pptx_asset.storage_path).stat().st_size == 0:
        issues.append(_issue("high", "artifact", "PPTX 文件为空。"))

    if slides:
        _check_slide_text(slides, issues, suggestions)
        _check_layout_rhythm(slides, suggestions)
        _check_design_signals(slides, suggestions)
        _check_detail_depth(slides, suggestions)
    else:
        issues.append(_issue("medium", "deck_ir", "Deck IR 中没有可审阅的 slides。"))

    _check_preview(preview, workspace, suggestions)

    if not suggestions:
        suggestions.append("当前结构可以作为初稿；下一步建议加入预览图渲染 QA。")

    return {
        "schema_version": "1",
        "deck_id": str(deck.id),
        "deck_title": deck.title,
        "slide_count": len(slides),
        "artifacts": {
            "deck_ir": deck_ir_asset.storage_path if deck_ir_asset else None,
            "pptx": pptx_asset.storage_path if pptx_asset else None,
        },
        "preview": preview.qa_payload(workspace),
        "issues": issues,
        "suggestions": suggestions,
        "memory_signals": _memory_signals(slides),
    }


def _slides(deck_payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not deck_payload:
        return []
    slides = deck_payload.get("slides")
    if not isinstance(slides, list):
        return []
    return [slide for slide in slides if isinstance(slide, dict)]


def _check_slide_text(
    slides: list[dict[str, Any]],
    issues: list[dict[str, str]],
    suggestions: list[str],
) -> None:
    content_slides = [slide for slide in slides if slide.get("layout") not in {"cover", "thanks"}]
    for idx, slide in enumerate(content_slides, start=1):
        title = str(slide.get("title") or "")
        bullets = [str(item) for item in slide.get("bullets") or []]
        if not title.strip():
            issues.append(_issue("medium", f"slide:{idx}", "内容页缺少标题。"))
        if len(title) > 34:
            suggestions.append(f"第 {idx} 张标题偏长，可压缩为一句核心判断。")
        if len(bullets) > 4:
            suggestions.append(f"第 {idx} 张 bullet 较多，可改成卡片或流程布局。")
        for bullet in bullets:
            if len(bullet) > 74:
                suggestions.append(f"第 {idx} 张存在长 bullet，建议拆短：{bullet[:32]}...")
                break


def _check_layout_rhythm(slides: list[dict[str, Any]], suggestions: list[str]) -> None:
    content_layouts = [
        str(slide.get("layout") or "")
        for slide in slides
        if slide.get("layout") not in {"cover", "thanks"}
    ]
    if len(content_layouts) >= 4 and len(set(content_layouts)) <= 1:
        suggestions.append("版式节奏偏单一，建议加入 timeline、process cards 或 fact cards。")
    rhythms = [
        str(slide.get("visual") or slide.get("layout") or "")
        for slide in slides
        if slide.get("layout") not in {"cover", "thanks"}
    ]
    for idx in range(0, max(0, len(rhythms) - 2)):
        if rhythms[idx] and len({rhythms[idx], rhythms[idx + 1], rhythms[idx + 2]}) == 1:
            suggestions.append(
                f"第 {idx + 1}-{idx + 3} 张视觉节奏连续重复，可换成 stat_callout、quote_block、table 或 process。"
            )
            break


def _check_design_signals(slides: list[dict[str, Any]], suggestions: list[str]) -> None:
    content_slides = [
        slide
        for slide in slides
        if slide.get("layout") not in {"cover", "toc", "section", "thanks"}
    ]
    if not content_slides:
        return

    missing_visual = [idx for idx, slide in _numbered_content_slides(slides) if not slide.get("visual")]
    if missing_visual:
        shown = "、".join(str(idx) for idx in missing_visual[:4])
        suggestions.append(f"第 {shown} 张缺少组件信号；建议 Hermes 明确写 `组件：...`。")

    missing_support = [
        idx
        for idx, slide in _numbered_content_slides(slides)
        if not _slide_support(slide) and slide.get("visual") not in {"table", "timeline", "stat_callout"}
    ]
    if missing_support:
        shown = "、".join(str(idx) for idx in missing_support[:4])
        suggestions.append(f"第 {shown} 张缺少支撑/展开对象；建议补 `支撑：案例、步骤、定义、数据或行动项`。")


def _check_detail_depth(slides: list[dict[str, Any]], suggestions: list[str]) -> None:
    shallow: list[int] = []
    for idx, slide in _numbered_content_slides(slides):
        if slide.get("visual") in {"quote_block", "stat_callout"}:
            continue
        if _detail_units(slide) < 3:
            shallow.append(idx)
    if shallow:
        shown = "、".join(str(idx) for idx in shallow[:4])
        suggestions.append(f"第 {shown} 张展开偏薄；建议每页至少 3 个具体分点或 2 个分点加案例/步骤。")


def _detail_units(slide: dict[str, Any]) -> int:
    total = len([item for item in slide.get("bullets") or [] if str(item).strip()])
    if _slide_support(slide):
        total += 1
    total += sum(
        len([item for item in (column.get("bullets") or []) if str(item).strip()])
        for column in slide.get("columns") or []
        if isinstance(column, dict)
    )
    total += len([item for item in slide.get("items") or [] if isinstance(item, dict) and item.get("desc")])
    table = slide.get("table")
    if isinstance(table, dict):
        total += len(table.get("rows") or [])
    return total


def _slide_support(slide: dict[str, Any]) -> str:
    return str(slide.get("support") or slide.get("proof") or "").strip()


def _numbered_content_slides(slides: list[dict[str, Any]]) -> list[tuple[int, dict[str, Any]]]:
    numbered: list[tuple[int, dict[str, Any]]] = []
    content_index = 0
    for slide in slides:
        if slide.get("layout") in {"cover", "toc", "section", "thanks"}:
            continue
        content_index += 1
        numbered.append((content_index, slide))
    return numbered


def _check_preview(
    preview: PreviewArtifacts,
    workspace: Path,
    suggestions: list[str],
) -> None:
    payload = preview.qa_payload(workspace)
    if payload["contact_sheet_rendered"]:
        suggestions.append(f"已生成 contact sheet：{payload['contact_sheet']}，可用于人工或视觉模型审查。")
        return
    if payload["pdf_rendered"]:
        suggestions.append("已生成 PDF 预览；缺少 PNG/contact sheet 时仍可进行人工快速检查。")
        return
    if payload["warnings"]:
        suggestions.append("未生成可视化预览；请检查渲染工具链或在服务器安装 poppler-utils/Pillow。")


def _memory_signals(slides: list[dict[str, Any]]) -> list[str]:
    joined = "\n".join(
        str(slide.get("title") or "") + "\n" + "\n".join(str(item) for item in slide.get("bullets") or [])
        for slide in slides
    )
    signals: list[str] = []
    if "计算材料" in joined or "DFT" in joined or "MD" in joined:
        signals.append("可能是计算材料/科研组会场景，后续可优先使用学术克制风格。")
    if "Agent" in joined or "Hermes" in joined:
        signals.append("用户关注 Agent 工作流，可保留流程图、记忆和验证闭环表达。")
    if not signals:
        signals.append("暂无明确长期偏好；等待用户显式反馈后再写入记忆。")
    return signals


def _render_report(deck: DeckSession, qa: dict[str, Any]) -> str:
    issues = qa["issues"]
    suggestions = qa["suggestions"]
    memory_signals = qa["memory_signals"]
    preview = qa["preview"]
    status = "需要处理" if issues else "结构可用"
    lines = [
        "# Hermes PPT Review",
        "",
        "## Summary",
        "",
        f"- Deck: {deck.title}",
        f"- Status: {status}",
        f"- Slide count: {qa['slide_count']}",
        "- Mode: deterministic preflight for Hermes review",
        "",
        "## Must Fix",
        "",
    ]
    if issues:
        lines.extend(f"- [{item['severity']}] {item['message']}" for item in issues)
    else:
        lines.append("- No blocking issue found by deterministic QA.")
    lines.extend(["", "## Suggested Repairs", ""])
    lines.extend(f"- {item}" for item in suggestions)
    lines.extend(
        [
            "",
            "## Preview QA",
            "",
            f"- PDF rendered: {preview['pdf_rendered']}",
            f"- Page images: {preview['page_images_count']}",
            f"- Contact sheet: {preview['contact_sheet'] or 'not available'}",
        ]
    )
    if preview["warnings"]:
        lines.append(f"- Warnings: {'; '.join(preview['warnings'])}")
    lines.extend(["", "## Memory Signals", ""])
    lines.extend(f"- {item}" for item in memory_signals)
    lines.extend(
        [
            "",
            "## Next Step",
            "",
            "When Hermes is enabled for production review, load the `aippt-sjtu-ppt` skill,",
            "read this report plus `qa/qa.json`, and write either `logs/hermes_review.md`",
            "or a validated `ir/deck.repaired.json` proposal.",
            "",
        ]
    )
    return "\n".join(lines)


def _issue(severity: str, category: str, message: str) -> dict[str, str]:
    return {"severity": severity, "category": category, "message": message}
