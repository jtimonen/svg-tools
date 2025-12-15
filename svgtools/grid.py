import copy
import re
from pathlib import Path
import xml.etree.ElementTree as ET

from .svg import NS, SVG_TAG, parse_length, parse_viewbox


def _split_defs_and_body(root: ET.Element):
    defs = []
    body = []
    for child in list(root):
        if child.tag == f"{SVG_TAG}defs":
            defs.append(child)
        else:
            body.append(child)
    return defs, body


def _make_cell_group(body_nodes, tx, ty, vb_min_x, vb_min_y, scale_x, scale_y, row=None, col=None):
    attrib = {"transform": f"translate({tx},{ty})"}
    if row is not None:
        attrib["data-row"] = str(row)
    if col is not None:
        attrib["data-col"] = str(col)
    group = ET.Element(f"{SVG_TAG}g", attrib)
    inner = ET.SubElement(group, f"{SVG_TAG}g", {"transform": f"translate({-vb_min_x},{-vb_min_y}) scale({scale_x},{scale_y})"})
    for node in body_nodes:
        inner.append(copy.deepcopy(node))
    return group


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

    defs, body = _split_defs_and_body(root)

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

    # Keep original defs once
    new_defs = ET.SubElement(new_root, f"{SVG_TAG}defs")
    for d in defs:
        for node in list(d):
            new_defs.append(copy.deepcopy(node))

    for r in range(rows):
        for c in range(cols):
            tx = c * cell_width
            ty = r * cell_height
            cell_group = _make_cell_group(body, tx, ty, vb_min_x, vb_min_y, scale_x, scale_y, row=r, col=c)
            new_root.append(cell_group)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(new_root).write(out_path, encoding="utf-8", xml_declaration=True)
    return out_path


def move_tile(svg_path: Path, grid_size: float, src_row: int, src_col: int, dst_row: int, dst_col: int, out_path: Path):
    """Copy tile at (src_row, src_col) to (dst_row, dst_col) in an existing grid SVG, preserving content."""
    ET.register_namespace("", NS["svg"])
    ET.register_namespace("xlink", NS["xlink"])

    tree = ET.parse(svg_path)
    root = tree.getroot()

    def parse_transform_to_rc(node):
        tr = node.attrib.get("transform", "")
        m = re.search(r"translate\(\s*([-\d\.]+)[ ,]+([-\d\.]+)\s*\)", tr)
        if not m:
            return None
        tx = float(m.group(1))
        ty = float(m.group(2))
        col = round(tx / grid_size)
        row = round(ty / grid_size)
        return row, col

    def match_cell(node, r, c):
        r_attr = node.attrib.get("data-row")
        c_attr = node.attrib.get("data-col")
        if r_attr is not None and c_attr is not None:
            return int(r_attr) == r and int(c_attr) == c
        rc = parse_transform_to_rc(node)
        return rc == (r, c)

    cells = [n for n in root if n.tag == f"{SVG_TAG}g"]
    src = next((n for n in cells if match_cell(n, src_row, src_col)), None)
    dst = next((n for n in cells if match_cell(n, dst_row, dst_col)), None)

    if src is None:
        raise ValueError(f"Source cell ({src_row},{src_col}) not found")
    if dst is None:
        raise ValueError(f"Destination cell ({dst_row},{dst_col}) not found")

    # Replace dst inner content with deep copy of src inner content
    dst_children = list(dst)
    if not dst_children:
        raise ValueError("Destination cell has no inner group to replace")
    dst_inner = dst_children[-1]
    if dst_inner.tag != f"{SVG_TAG}g":
        raise ValueError("Unexpected destination structure; expected inner group")

    src_children = list(src)
    if not src_children:
        raise ValueError("Source cell has no inner group to copy")
    src_inner = src_children[-1]
    if src_inner.tag != f"{SVG_TAG}g":
        raise ValueError("Unexpected source structure; expected inner group")

    # Clear destination inner group and copy children
    for ch in list(dst_inner):
        dst_inner.remove(ch)
    for ch in list(src_inner):
        dst_inner.append(copy.deepcopy(ch))

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(out_path, encoding="utf-8", xml_declaration=True)
    return out_path
