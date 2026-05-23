from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from .constants import BG_LIGHT, CONTENT_LEFT_IN, CONTENT_TOP_IN, CONTENT_W_IN, GOLD, SJTU_RED, TEXT_MAIN, WHITE
from .schema import Deck, Layout, Slide


def rgb(hex_color: str) -> RGBColor:
    return RGBColor.from_string(hex_color)


def build_pptx(deck: Deck, output_path: str | Path) -> Path:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    for idx, slide in enumerate(deck.slides, start=1):
        render_slide(prs, slide, idx)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    prs.save(output)
    return output


def render_slide(prs: Presentation, slide_data: Slide, page_num: int) -> None:
    blank = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank)

    if slide_data.layout == Layout.COVER:
        render_cover(slide, slide_data)
    elif slide_data.layout == Layout.THANKS:
        render_thanks(slide, slide_data)
    else:
        render_header(slide, slide_data.title)
        render_body(slide, slide_data)
        render_footer(slide, page_num)


def render_cover(slide, slide_data: Slide) -> None:
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = rgb(SJTU_RED)
    title = slide.shapes.add_textbox(Inches(1.0), Inches(2.3), Inches(11.3), Inches(1.0))
    p = title.text_frame.paragraphs[0]
    p.text = slide_data.title
    p.font.size = Pt(34)
    p.font.bold = True
    p.font.color.rgb = rgb(WHITE)
    p.alignment = PP_ALIGN.CENTER

    subtitle = slide.shapes.add_textbox(Inches(1.3), Inches(3.5), Inches(10.7), Inches(0.7))
    p = subtitle.text_frame.paragraphs[0]
    p.text = slide_data.subtitle
    p.font.size = Pt(18)
    p.font.color.rgb = rgb(WHITE)
    p.alignment = PP_ALIGN.CENTER


def render_thanks(slide, slide_data: Slide) -> None:
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = rgb(SJTU_RED)
    box = slide.shapes.add_textbox(Inches(1.0), Inches(2.8), Inches(11.3), Inches(1.1))
    p = box.text_frame.paragraphs[0]
    p.text = slide_data.title or "谢谢"
    p.font.size = Pt(38)
    p.font.bold = True
    p.font.color.rgb = rgb(WHITE)
    p.alignment = PP_ALIGN.CENTER


def render_header(slide, title: str) -> None:
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0),
        Inches(0),
        Inches(13.333),
        Inches(0.88),
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = rgb(SJTU_RED)
    bar.line.fill.background()
    box = slide.shapes.add_textbox(Inches(0.72), Inches(0.17), Inches(11.8), Inches(0.5))
    p = box.text_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = rgb(WHITE)


def render_body(slide, slide_data: Slide) -> None:
    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(CONTENT_LEFT_IN),
        Inches(CONTENT_TOP_IN),
        Inches(CONTENT_W_IN),
        Inches(5.35),
    )
    card.fill.solid()
    card.fill.fore_color.rgb = rgb(BG_LIGHT)
    card.line.color.rgb = rgb(GOLD)

    box = slide.shapes.add_textbox(Inches(1.1), Inches(1.55), Inches(11.1), Inches(4.6))
    frame = box.text_frame
    frame.word_wrap = True
    content = slide_data.bullets or [c.heading for c in slide_data.columns if c.heading]
    for idx, bullet in enumerate(content):
        p = frame.paragraphs[0] if idx == 0 else frame.add_paragraph()
        p.text = bullet
        p.level = 0
        p.font.size = Pt(18)
        p.font.color.rgb = rgb(TEXT_MAIN)
        p.space_after = Pt(10)

    if slide_data.insight:
        insight = slide.shapes.add_textbox(Inches(1.1), Inches(6.25), Inches(11.0), Inches(0.45))
        p = insight.text_frame.paragraphs[0]
        p.text = slide_data.insight
        p.font.size = Pt(13)
        p.font.color.rgb = rgb(SJTU_RED)


def render_footer(slide, page_num: int) -> None:
    box = slide.shapes.add_textbox(Inches(12.0), Inches(6.9), Inches(0.7), Inches(0.3))
    p = box.text_frame.paragraphs[0]
    p.text = str(page_num)
    p.font.size = Pt(9)
    p.font.color.rgb = rgb(TEXT_MAIN)
    p.alignment = PP_ALIGN.RIGHT
