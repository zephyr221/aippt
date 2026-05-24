import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import Settings


@dataclass(frozen=True)
class PreviewArtifacts:
    enabled: bool
    pdf_path: Path | None
    page_paths: tuple[Path, ...]
    contact_sheet_path: Path | None
    warnings: tuple[str, ...]
    tools: dict[str, str | bool | None]

    def best_download(self) -> tuple[Path, str] | None:
        if self.contact_sheet_path is not None:
            return self.contact_sheet_path, "image/png"
        if self.pdf_path is not None:
            return self.pdf_path, "application/pdf"
        return None

    def qa_payload(self, workspace: Path) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "pdf_rendered": self.pdf_path is not None,
            "pdf": _relative_path(workspace, self.pdf_path),
            "page_images_count": len(self.page_paths),
            "page_images": [_relative_path(workspace, path) for path in self.page_paths],
            "contact_sheet_rendered": self.contact_sheet_path is not None,
            "contact_sheet": _relative_path(workspace, self.contact_sheet_path),
            "warnings": list(self.warnings),
            "tools": self.tools,
        }


def build_preview_artifacts(
    settings: Settings,
    pptx_path: Path | None,
    workspace: Path,
) -> PreviewArtifacts:
    warnings: list[str] = []
    tools: dict[str, str | bool | None] = {
        "soffice": _command_path(settings.preview_soffice_command, fallback="libreoffice"),
        "pdftoppm": _command_path(settings.preview_pdftoppm_command),
        "pillow": _has_pillow(),
    }

    if not settings.preview_render_enabled:
        return PreviewArtifacts(False, None, (), None, ("Preview rendering is disabled.",), tools)

    if pptx_path is None or not pptx_path.is_file():
        return PreviewArtifacts(True, None, (), None, ("PPTX file is not available.",), tools)

    preview_dir = workspace / "preview"
    preview_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = _render_pdf(settings, pptx_path, preview_dir, tools, warnings)
    page_paths: tuple[Path, ...] = ()
    contact_sheet_path: Path | None = None

    if pdf_path is not None:
        page_paths = _render_png_pages(settings, pdf_path, preview_dir, tools, warnings)
        if page_paths:
            contact_sheet_path = _render_contact_sheet(
                settings,
                page_paths,
                preview_dir / "contact-sheet.png",
                tools,
                warnings,
            )

    return PreviewArtifacts(True, pdf_path, page_paths, contact_sheet_path, tuple(warnings), tools)


def _render_pdf(
    settings: Settings,
    pptx_path: Path,
    preview_dir: Path,
    tools: dict[str, str | bool | None],
    warnings: list[str],
) -> Path | None:
    soffice = tools["soffice"]
    if not isinstance(soffice, str):
        warnings.append("LibreOffice/soffice is not available; skipped PDF preview rendering.")
        return None

    pdf_path = preview_dir / f"{pptx_path.stem}.pdf"
    pdf_path.unlink(missing_ok=True)
    profile_dir = preview_dir / "libreoffice-profile"
    profile_dir.mkdir(exist_ok=True)
    command = [
        soffice,
        "--headless",
        "--nologo",
        "--nofirststartwizard",
        f"-env:UserInstallation={profile_dir.resolve().as_uri()}",
        "--convert-to",
        "pdf",
        "--outdir",
        str(preview_dir),
        str(pptx_path),
    ]
    result = _run_command(command, settings.worker_command_timeout_seconds)
    if result.returncode != 0:
        warnings.append(f"LibreOffice PDF render failed: {result.stderr or result.stdout}".strip())
        return None
    if not pdf_path.is_file():
        warnings.append("LibreOffice did not produce the expected PDF preview.")
        return None
    return pdf_path


def _render_png_pages(
    settings: Settings,
    pdf_path: Path,
    preview_dir: Path,
    tools: dict[str, str | bool | None],
    warnings: list[str],
) -> tuple[Path, ...]:
    pdftoppm = tools["pdftoppm"]
    if not isinstance(pdftoppm, str):
        warnings.append("pdftoppm is not available; skipped page PNG rendering.")
        return ()

    pages_dir = preview_dir / "pages"
    pages_dir.mkdir(exist_ok=True)
    for old_png in pages_dir.glob("*.png"):
        old_png.unlink()

    base = pages_dir / "slide"
    command = [
        pdftoppm,
        "-png",
        "-r",
        str(settings.preview_render_dpi),
        "-f",
        "1",
        "-l",
        str(settings.preview_max_pages),
        str(pdf_path),
        str(base),
    ]
    result = _run_command(command, settings.worker_command_timeout_seconds)
    if result.returncode != 0:
        warnings.append(f"PDF to PNG render failed: {result.stderr or result.stdout}".strip())
        return ()

    generated = sorted(pages_dir.glob("slide-*.png"), key=_page_number)
    renamed: list[Path] = []
    for index, path in enumerate(generated, start=1):
        target = pages_dir / f"slide-{index:02d}.png"
        if path != target:
            target.unlink(missing_ok=True)
            path.replace(target)
        renamed.append(target)
    return tuple(renamed)


def _render_contact_sheet(
    settings: Settings,
    page_paths: tuple[Path, ...],
    output_path: Path,
    tools: dict[str, str | bool | None],
    warnings: list[str],
) -> Path | None:
    if tools["pillow"] is not True:
        warnings.append("Pillow is not available; skipped contact sheet rendering.")
        return None
    try:
        _write_contact_sheet(page_paths, output_path, settings.preview_contact_sheet_thumb_width)
    except OSError as exc:
        warnings.append(f"Contact sheet rendering failed: {exc}")
        return None
    return output_path if output_path.is_file() else None


def _write_contact_sheet(
    page_paths: tuple[Path, ...],
    output_path: Path,
    thumb_width: int,
) -> None:
    from PIL import Image, ImageDraw, ImageFont

    if not page_paths:
        raise OSError("no page images")

    images = [Image.open(path).convert("RGB") for path in page_paths]
    try:
        ratio = images[0].height / images[0].width
        thumb_height = max(1, round(thumb_width * ratio))
        thumbs = [
            image.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
            for image in images
        ]
        columns = min(4, max(1, math.ceil(math.sqrt(len(thumbs)))))
        rows = math.ceil(len(thumbs) / columns)
        margin = 24
        gap = 20
        label_height = 28
        canvas_width = margin * 2 + columns * thumb_width + (columns - 1) * gap
        canvas_height = margin * 2 + rows * (thumb_height + label_height) + (rows - 1) * gap
        canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
        draw = ImageDraw.Draw(canvas)
        font = ImageFont.load_default()

        for index, thumb in enumerate(thumbs, start=1):
            row = (index - 1) // columns
            column = (index - 1) % columns
            x = margin + column * (thumb_width + gap)
            y = margin + row * (thumb_height + label_height + gap)
            draw.text((x, y), f"Slide {index}", fill=(40, 40, 40), font=font)
            image_y = y + label_height
            canvas.paste(thumb, (x, image_y))
            draw.rectangle(
                (x, image_y, x + thumb_width - 1, image_y + thumb_height - 1),
                outline=(210, 210, 210),
                width=1,
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output_path)
    finally:
        for image in images:
            image.close()


def _run_command(command: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(
            command,
            returncode=124,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "command timed out",
        )


def _command_path(command: str, fallback: str | None = None) -> str | None:
    resolved = shutil.which(command)
    if resolved:
        return resolved
    path = Path(command)
    if path.is_file():
        return str(path)
    if fallback:
        return shutil.which(fallback)
    return None


def _has_pillow() -> bool:
    try:
        import PIL  # noqa: F401
    except ImportError:
        return False
    return True


def _page_number(path: Path) -> int:
    try:
        return int(path.stem.rsplit("-", maxsplit=1)[-1])
    except ValueError:
        return 0


def _relative_path(workspace: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return path.relative_to(workspace).as_posix()
    except ValueError:
        return path.name
