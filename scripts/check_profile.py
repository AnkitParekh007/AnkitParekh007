#!/usr/bin/env python3
"""Fast, dependency-free structural QA for GitHub profile assets and README."""
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
readme = (ROOT / "README.md").read_text(encoding="utf-8")
errors = []

def check(condition, description):
    if not condition:
        errors.append(description)

svg_files = ["assets/ai-architect-banner.svg", "assets/enterprise-ai-architecture.svg"]
for name in svg_files:
    file = ROOT / name
    check(file.is_file(), f"Missing SVG: {name}")
    if not file.is_file():
        continue
    try:
        root = ET.parse(file).getroot()
        check(root.tag.endswith("}svg") or root.tag == "svg", f"Invalid SVG root: {name}")
        check(bool(root.attrib.get("viewBox")), f"Missing responsive viewBox: {name}")
        check(any(node.tag.endswith("title") for node in root.iter()), f"Missing accessible title: {name}")
        check(name in readme, f"README does not embed {name}")
    except ET.ParseError as exc:
        errors.append(f"Invalid SVG XML in {name}: {exc}")

# Named anchors are deliberately explicit so GitHub heading slug changes cannot break nav.
anchors = set(re.findall(r'<a\s+id="([^"]+)"', readme))
links = re.findall(r'href="#([^"]+)"', readme)
for target in links:
    check(unquote(target) in anchors, f"Unresolved in-page navigation target: #{target}")

images = re.findall(r"<img\s+[^>]*>", readme, re.IGNORECASE)
check(len(images) >= 2, "Expected both banner and architecture images")
for image in images:
    check(bool(re.search(r'\balt="[^"]+"', image)), f"Missing non-empty image alt: {image[:90]}")

check("Live copilot demo" in readme, "Missing recruiter first-screen demo CTA")
check("Engineering leadership & impact" in readme, "Missing leadership evidence section")
check("Verifiable engineering evidence" in readme, "Missing evidence section")
check("# Hi, I'm Ankit" not in readme, "Duplicate H1 below the SVG banner")

for label, target in [
    ("featured", "featured-projects"),
    ("architecture", "architecture"),
    ("expertise", "expertise"),
    ("review", "review-path"),
]:
    check(target in anchors, f"Missing anchor: {label}")

if errors:
    print("Profile checks FAILED:")
    for item in errors:
        print(f" - {item}")
    sys.exit(1)
print(f"Profile checks PASSED: {len(svg_files)} SVG assets, {len(anchors)} anchors, {len(images)} images.")
