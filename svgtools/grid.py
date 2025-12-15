import copy
from pathlib import Path
import xml.etree.ElementTree as ET

from .svg import NS, SVG_TAG, parse_length, parse_viewbox


def create_grid_svg(svg_path: Path, rows: int, cols: int, out_path: Path):
    if rows < 1 or cols < 1:
        raise ValueError("rows and cols must be >= 1")

    tree = ET.parse(svg_path)
    root = tree.getroot()

    vb_min_x, vb_min_y, vb_width, vb_height = parse_viewbox(root)
    width_attr = root.attrib.get("width")
    height_attr = root.attrib.get("height")
    cell_width = parse_length(width_attr, vb_width)
    cell_height = parse_length(height_attr, vb_height)

    scale_x = cell_width / vb_width if vb_width else 1.0
    scale_y = cell_height / vb_height if vb_height else 1.0

    ET.register_namespace("", NS["svg"])
    ET.register_namespace("xlink", NS["xlink"])

    new_root = ET.Element(
        f"{SVG_TAG}svg",
        {
            "width": str(cell_width * cols),
            "height": str(cell_height * rows),
            "viewBox": f"0 0 {cell_width * cols} {cell_height * rows}",
            "version": root.attrib.get("version", "1.1"),
        },
    )

    if "preserveAspectRatio" in root.attrib:
        new_root.set("preserveAspectRatio", root.attrib["preserveAspectRatio"])

    defs = ET.SubElement(new_root, f"{SVG_TAG}defs")
    tile = ET.SubElement(
        defs,
        f"{SVG_TAG}g",
        {
            "id": "tile",
            "transform": f"translate({-vb_min_x},{-vb_min_y}) scale({scale_x},{scale_y})",
        },
    )
    for child in list(root):
        tile.append(copy.deepcopy(child))

    for r in range(rows):
        for c in range(cols):
            tx = c * cell_width
            ty = r * cell_height
            ET.SubElement(
                new_root,
                f"{SVG_TAG}use",
                {
                    f"{{{NS['xlink']}}}href": "#tile",
                    "href": "#tile",  # SVG2
                    "transform": f"translate({tx},{ty})",
                },
            )

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(new_root).write(out_path, encoding="utf-8", xml_declaration=True)
    return out_path
