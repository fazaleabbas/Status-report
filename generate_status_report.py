from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

COLORS = {
    "navy": RGBColor(15, 37, 64),
    "blue": RGBColor(35, 90, 166),
    "light_blue": RGBColor(232, 240, 252),
    "text": RGBColor(51, 65, 85),
    "muted": RGBColor(100, 116, 139),
    "border": RGBColor(203, 213, 225),
    "green": RGBColor(46, 125, 50),
    "amber": RGBColor(249, 168, 37),
    "red": RGBColor(198, 40, 40),
    "white": RGBColor(255, 255, 255),
    "light_gray": RGBColor(248, 250, 252),
}

RAG_LABELS = {
    "green": "On Track",
    "amber": "In Progress / Dependent",
    "red": "At Risk",
}

VALID_RAGS = {"green", "amber", "red"}

RED_KEYWORDS = [
    "risk",
    "blocked",
    "blocker",
    "delay",
    "issue",
    "pending",
    "removed",
    "security",
]

GREEN_KEYWORDS = [
    "done",
    "complete",
    "completed",
    "on track",
    "certified",
    "shipped",
]


def load_data(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_simple_data(path: Path) -> list[dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Simple input JSON must be a list of objects with 'name' and 'status'.")
    projects: list[dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Each simple input item must be an object.")
        name = str(item.get("name", "")).strip()
        status = str(item.get("status", "")).strip()
        if not name or not status:
            raise ValueError("Each simple input item must include non-empty 'name' and 'status'.")
        raw_rag = str(item.get("rag", "")).strip().lower()
        rag = ""
        if raw_rag:
            if raw_rag == "auto":
                rag = ""
            elif raw_rag in VALID_RAGS:
                rag = raw_rag
            else:
                raise ValueError("Optional 'rag' must be one of: green, amber, red, auto.")

        project = {"name": name, "status": status}
        if rag:
            project["rag"] = rag
        projects.append(project)
    return projects


def infer_rag_from_status(status: str) -> str:
    text = status.lower()
    if any(keyword in text for keyword in RED_KEYWORDS):
        return "red"
    if any(keyword in text for keyword in GREEN_KEYWORDS):
        return "green"
    return "amber"


def build_data_from_simple_projects(
    simple_projects: list[dict[str, str]],
    report_title: str,
    report_date: str,
) -> dict[str, Any]:
    projects: list[dict[str, Any]] = []
    for item in simple_projects:
        rag = item.get("rag") or infer_rag_from_status(item["status"])
        projects.append(
            {
                "name": item["name"],
                "rag": rag,
                "progress": "Status Update",
                "status": item["status"],
                "next_step": "Confirm next milestone and owner for this project.",
                "notes": [
                    "Update captured directly from the project status input form.",
                    "Review this project in the next reporting cycle.",
                ],
            }
        )

    green_count = sum(1 for project in projects if project["rag"] == "green")
    amber_count = sum(1 for project in projects if project["rag"] == "amber")
    red_count = sum(1 for project in projects if project["rag"] == "red")
    portfolio_summary = (
        f"Portfolio snapshot: {green_count} on track, {amber_count} in progress, "
        f"and {red_count} at risk based on the latest user-entered updates."
    )

    return {
        "report_title": report_title,
        "report_date": report_date,
        "portfolio_summary": portfolio_summary,
        "projects": projects,
    }


def rag_color(rag: str) -> RGBColor:
    return COLORS[rag]



def add_background(slide) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = COLORS["white"]



def add_title(slide, title: str, subtitle: str | None = None) -> None:
    title_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.35), Inches(9.8), Inches(0.75))
    tf = title_box.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = title
    run.font.name = "Aptos Display"
    run.font.size = Pt(24)
    run.font.bold = True
    run.font.color.rgb = COLORS["navy"]
    if subtitle:
        subtitle_box = slide.shapes.add_textbox(Inches(0.62), Inches(1.0), Inches(9.5), Inches(0.35))
        tf2 = subtitle_box.text_frame
        p2 = tf2.paragraphs[0]
        r2 = p2.add_run()
        r2.text = subtitle
        r2.font.name = "Aptos"
        r2.font.size = Pt(11)
        r2.font.color.rgb = COLORS["muted"]

    line = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(0.6), Inches(1.28), Inches(12.1), Inches(0.04))
    line.fill.solid()
    line.fill.fore_color.rgb = COLORS["blue"]
    line.line.fill.background()



def add_textbox(slide, left, top, width, height, text: str, font_size=14, color_key="text", bold=False) -> None:
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = text
    run.font.name = "Aptos"
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.color.rgb = COLORS[color_key]



def add_bullets(slide, left, top, width, height, bullets: list[str], font_size=14, color_key="text") -> None:
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    for index, bullet in enumerate(bullets):
        p = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
        p.text = bullet
        p.level = 0
        p.font.name = "Aptos"
        p.font.size = Pt(font_size)
        p.font.color.rgb = COLORS[color_key]
        p.bullet = True
        p.space_after = Pt(4)



def add_rag_chip(slide, left, top, rag: str, label: str | None = None, width=Inches(1.55)) -> None:
    circle = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.OVAL, left, top, Inches(0.24), Inches(0.24))
    circle.fill.solid()
    circle.fill.fore_color.rgb = rag_color(rag)
    circle.line.color.rgb = rag_color(rag)

    chip = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, left + Inches(0.3), top - Inches(0.03), width, Inches(0.3))
    chip.fill.solid()
    chip.fill.fore_color.rgb = COLORS["light_gray"]
    chip.line.color.rgb = COLORS["border"]
    tf = chip.text_frame
    tf.clear()
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = label or RAG_LABELS[rag]
    run.font.name = "Aptos"
    run.font.size = Pt(10)
    run.font.bold = True
    run.font.color.rgb = COLORS["text"]



def add_summary_card(slide, left, top, width, height, heading: str, value: str, accent: RGBColor) -> None:
    card = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = COLORS["white"]
    card.line.color.rgb = COLORS["border"]

    accent_bar = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, left, top, Inches(0.08), height)
    accent_bar.fill.solid()
    accent_bar.fill.fore_color.rgb = accent
    accent_bar.line.fill.background()

    add_textbox(slide, left + Inches(0.18), top + Inches(0.18), width - Inches(0.3), Inches(0.25), heading.upper(), 9, "muted", True)
    add_textbox(slide, left + Inches(0.18), top + Inches(0.5), width - Inches(0.3), Inches(0.55), value, 20, "navy", True)



def add_title_slide(prs: Presentation, data: dict[str, Any]) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide)

    banner = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(0), Inches(0), SLIDE_W, Inches(1.15))
    banner.fill.solid()
    banner.fill.fore_color.rgb = COLORS["navy"]
    banner.line.fill.background()

    add_textbox(slide, Inches(0.75), Inches(1.55), Inches(9.0), Inches(0.8), data["report_title"], 26, "navy", True)
    add_textbox(slide, Inches(0.78), Inches(2.2), Inches(7.0), Inches(0.35), f"Reporting date: {data['report_date']}", 13, "muted")
    add_textbox(slide, Inches(0.78), Inches(2.75), Inches(11.0), Inches(1.0), data["portfolio_summary"], 20, "text")

    legend_top = Inches(4.6)
    add_textbox(slide, Inches(0.78), legend_top - Inches(0.35), Inches(3.0), Inches(0.25), "RAG legend", 12, "navy", True)
    add_rag_chip(slide, Inches(0.78), legend_top, "green")
    add_rag_chip(slide, Inches(3.0), legend_top, "amber")
    add_rag_chip(slide, Inches(5.55), legend_top, "red")

    footer = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, Inches(8.8), Inches(5.0), Inches(3.6), Inches(1.4))
    footer.fill.solid()
    footer.fill.fore_color.rgb = COLORS["light_blue"]
    footer.line.color.rgb = COLORS["border"]
    add_textbox(slide, Inches(9.1), Inches(5.35), Inches(3.0), Inches(0.7), "Executive project update deck", 18, "blue", True)



def add_overview_slide(prs: Presentation, data: dict[str, Any]) -> None:
    projects = data["projects"]
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide)
    add_title(slide, "Executive summary", "Portfolio-level view of progress and attention areas")

    green_count = sum(1 for project in projects if project["rag"] == "green")
    amber_count = sum(1 for project in projects if project["rag"] == "amber")
    red_count = sum(1 for project in projects if project["rag"] == "red")

    add_summary_card(slide, Inches(0.75), Inches(1.7), Inches(2.3), Inches(1.2), "On Track", str(green_count), COLORS["green"])
    add_summary_card(slide, Inches(3.35), Inches(1.7), Inches(2.3), Inches(1.2), "In Progress", str(amber_count), COLORS["amber"])
    add_summary_card(slide, Inches(5.95), Inches(1.7), Inches(2.3), Inches(1.2), "At Risk", str(red_count), COLORS["red"])

    add_textbox(slide, Inches(8.65), Inches(1.8), Inches(3.4), Inches(0.8), data["portfolio_summary"], 12, "text")

    table_top = Inches(3.2)
    headers = ["Project", "RAG", "Current status", "Next step"]
    col_lefts = [Inches(0.75), Inches(2.8), Inches(4.0), Inches(8.7)]
    col_widths = [Inches(2.0), Inches(0.95), Inches(4.45), Inches(3.6)]

    for left, width, header in zip(col_lefts, col_widths, headers):
        header_box = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, left, table_top, width, Inches(0.45))
        header_box.fill.solid()
        header_box.fill.fore_color.rgb = COLORS["navy"]
        header_box.line.fill.background()
        tf = header_box.text_frame
        tf.clear()
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = header
        run.font.name = "Aptos"
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = COLORS["white"]

    row_height = Inches(0.73)
    for idx, project in enumerate(projects):
        top = table_top + Inches(0.5) + row_height * idx
        fill_color = COLORS["white"] if idx % 2 == 0 else COLORS["light_gray"]
        row = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.RECTANGLE, Inches(0.75), top, Inches(11.55), row_height)
        row.fill.solid()
        row.fill.fore_color.rgb = fill_color
        row.line.color.rgb = COLORS["border"]

        add_textbox(slide, Inches(0.9), top + Inches(0.18), Inches(1.75), Inches(0.3), project["name"], 11, "text", True)
        add_rag_chip(slide, Inches(2.95), top + Inches(0.2), project["rag"], project["rag"].upper(), Inches(0.85))
        add_textbox(slide, Inches(4.1), top + Inches(0.12), Inches(4.35), Inches(0.52), project["status"], 10, "text")
        add_textbox(slide, Inches(8.8), top + Inches(0.12), Inches(3.25), Inches(0.52), project["next_step"], 10, "text")



def add_detail_slides(prs: Presentation, data: dict[str, Any]) -> None:
    projects = data["projects"]
    for batch_index in range(0, len(projects), 3):
        batch = projects[batch_index:batch_index + 3]
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        add_background(slide)
        add_title(slide, "Detailed project updates", f"Projects {batch_index + 1} to {batch_index + len(batch)}")

        card_lefts = [Inches(0.72), Inches(4.47), Inches(8.22)]
        for project, left in zip(batch, card_lefts):
            card = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, left, Inches(1.7), Inches(3.35), Inches(4.95))
            card.fill.solid()
            card.fill.fore_color.rgb = COLORS["white"]
            card.line.color.rgb = COLORS["border"]

            add_rag_chip(slide, left + Inches(0.22), Inches(1.95), project["rag"], project["progress"], Inches(1.55))
            add_textbox(slide, left + Inches(0.22), Inches(2.38), Inches(2.7), Inches(0.42), project["name"], 18, "navy", True)
            add_textbox(slide, left + Inches(0.22), Inches(2.9), Inches(2.9), Inches(1.2), project["status"], 12, "text")

            add_textbox(slide, left + Inches(0.22), Inches(4.02), Inches(2.0), Inches(0.2), "Key considerations", 10, "muted", True)
            add_bullets(slide, left + Inches(0.22), Inches(4.23), Inches(2.85), Inches(1.0), project["notes"], 10)

            next_step_box = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, left + Inches(0.18), Inches(5.7), Inches(2.95), Inches(0.7))
            next_step_box.fill.solid()
            next_step_box.fill.fore_color.rgb = COLORS["light_blue"]
            next_step_box.line.color.rgb = COLORS["border"]
            tf = next_step_box.text_frame
            tf.clear()
            tf.word_wrap = True
            p1 = tf.paragraphs[0]
            r1 = p1.add_run()
            r1.text = "Next step: "
            r1.font.name = "Aptos"
            r1.font.size = Pt(10)
            r1.font.bold = True
            r1.font.color.rgb = COLORS["blue"]
            r2 = p1.add_run()
            r2.text = project["next_step"]
            r2.font.name = "Aptos"
            r2.font.size = Pt(10)
            r2.font.color.rgb = COLORS["text"]



def add_risk_slide(prs: Presentation, data: dict[str, Any]) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_background(slide)
    add_title(slide, "Management attention", "Top risk and actions for the next two weeks")

    risk_project = next((project for project in data["projects"] if project["rag"] == "red"), None)
    if risk_project is None:
        risk_project = data["projects"][0]

    risk_panel = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.4), Inches(4.6))
    risk_panel.fill.solid()
    risk_panel.fill.fore_color.rgb = RGBColor(254, 242, 242)
    risk_panel.line.color.rgb = COLORS["red"]

    add_rag_chip(slide, Inches(1.05), Inches(2.08), "red", "CRITICAL", Inches(1.1))
    add_textbox(slide, Inches(1.05), Inches(2.55), Inches(4.0), Inches(0.4), risk_project["name"], 22, "navy", True)
    add_textbox(slide, Inches(1.05), Inches(3.0), Inches(4.6), Inches(1.4), risk_project["status"], 14, "text")
    add_textbox(slide, Inches(1.05), Inches(4.55), Inches(4.5), Inches(0.25), "Required next action", 11, "red", True)
    add_textbox(slide, Inches(1.05), Inches(4.85), Inches(4.7), Inches(0.8), risk_project["next_step"], 13, "text")

    priorities = [f"{project['name']}: {project['next_step']}" for project in data["projects"][:6]]

    action_panel = slide.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE, Inches(6.55), Inches(1.8), Inches(5.95), Inches(4.6))
    action_panel.fill.solid()
    action_panel.fill.fore_color.rgb = COLORS["white"]
    action_panel.line.color.rgb = COLORS["border"]
    add_textbox(slide, Inches(6.85), Inches(2.1), Inches(4.5), Inches(0.35), "Next 2 weeks priorities", 18, "navy", True)
    add_bullets(slide, Inches(6.85), Inches(2.65), Inches(5.2), Inches(3.2), priorities, 13)



def build_deck(data: dict[str, Any], output_path: Path) -> None:
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    add_title_slide(prs, data)
    add_overview_slide(prs, data)
    add_detail_slides(prs, data)
    add_risk_slide(prs, data)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(output_path)



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a PowerPoint status report with RAG indicators.")
    parser.add_argument(
        "--input",
        help="Path to the JSON file that contains the full status data structure.",
    )
    parser.add_argument(
        "--simple-input",
        help="Path to a JSON list with objects containing only 'name' and 'status'.",
    )
    parser.add_argument(
        "--title",
        default="Project Status Report",
        help="Report title used with --simple-input.",
    )
    parser.add_argument(
        "--report-date",
        default=datetime.now().strftime("%d %B %Y"),
        help="Report date label used with --simple-input.",
    )
    parser.add_argument(
        "--output",
        default=f"status-report-{datetime.now().date().isoformat()}.pptx",
        help="Path to the output PowerPoint file.",
    )
    return parser.parse_args()



def main() -> None:
    args = parse_args()
    output_path = Path(args.output).resolve()

    if args.input and args.simple_input:
        raise SystemExit("Use either --input or --simple-input, not both.")

    if args.simple_input:
        simple_input_path = Path(args.simple_input).resolve()
        simple_projects = load_simple_data(simple_input_path)
        data = build_data_from_simple_projects(simple_projects, args.title, args.report_date)
    else:
        input_path = Path(args.input).resolve() if args.input else Path("project_statuses.json").resolve()
        data = load_data(input_path)

    if not data.get("projects"):
        raise SystemExit("No projects found. Add at least one project before generating the deck.")

    build_deck(data, output_path)
    print(f"Created presentation: {output_path}")


if __name__ == "__main__":
    main()

