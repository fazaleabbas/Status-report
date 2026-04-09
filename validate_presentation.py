from __future__ import annotations

import argparse
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

REQUIRED_PHRASES = [
    "Executive summary",
    "Detailed project updates",
    "Management attention",
]



def extract_slide_texts(pptx_path: Path) -> list[str]:
    texts: list[str] = []
    with zipfile.ZipFile(pptx_path) as archive:
        slide_files = sorted(
            name for name in archive.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        )
        namespace = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
        for slide_file in slide_files:
            root = ET.fromstring(archive.read(slide_file))
            fragments = [node.text for node in root.findall(".//a:t", namespace) if node.text]
            texts.append(" ".join(fragments))
    return texts



def validate(pptx_path: Path, required_texts: list[str] | None = None) -> int:
    if not pptx_path.exists():
        print(f"ERROR: {pptx_path} does not exist.")
        return 1
    if not zipfile.is_zipfile(pptx_path):
        print(f"ERROR: {pptx_path} is not a valid .pptx/zip container.")
        return 1

    slide_texts = extract_slide_texts(pptx_path)
    if len(slide_texts) < 4:
        print(f"ERROR: Expected at least 4 slides, found {len(slide_texts)}.")
        return 1

    combined = "\n".join(slide_texts)
    phrases_to_check = REQUIRED_PHRASES + (required_texts or [])
    missing = [phrase for phrase in phrases_to_check if phrase not in combined]
    if missing:
        print("ERROR: Missing required text fragments:")
        for phrase in missing:
            print(f" - {phrase}")
        return 1

    print(f"Validation passed for {pptx_path}")
    print(f"Slides found: {len(slide_texts)}")
    return 0



def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a generated PowerPoint status report.")
    parser.add_argument("pptx_path", help="Path to the PowerPoint file to validate.")
    parser.add_argument(
        "--require-text",
        action="append",
        default=[],
        help="Additional text fragment that must exist in the presentation. Repeat this option as needed.",
    )
    args = parser.parse_args()
    raise SystemExit(validate(Path(args.pptx_path).resolve(), required_texts=args.require_text))


if __name__ == "__main__":
    main()

