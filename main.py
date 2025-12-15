import re
from pathlib import Path
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.transforms import Affine2D
from matplotlib.colors import to_rgba
from svgpath2mpl import parse_path


SVG_FILE = Path("../game-art/characters/hero.svg")
NS = {"svg": "http://www.w3.org/2000/svg"}
SVG_TAG = f"{{{NS['svg']}}}"


def parse_style(style_str):
    """Return fill and stroke colors from the style string."""
    style = {}
    for kv in style_str.split(";"):
        if ":" in kv:
            k, v = kv.split(":", 1)
            style[k.strip()] = v.strip()
    return style.get("fill"), style.get("stroke"), style.get("fill-opacity", 1)


def parse_transform(transform_str):
    """Handle matrix/translate/scale transforms into an Affine2D."""
    t = Affine2D()
    for name, args in re.findall(r"([a-zA-Z]+)\(([^)]*)\)", transform_str):
        vals = [float(v) for v in re.split(r"[ ,]+", args.strip()) if v]
        if name == "matrix" and len(vals) == 6:
            t = t + Affine2D([[vals[0], vals[2], vals[4]],
                               [vals[1], vals[3], vals[5]],
                               [0, 0, 1]])
        elif name == "translate":
            tx = vals[0]
            ty = vals[1] if len(vals) > 1 else 0
            t = t.translate(tx, ty)
        elif name == "scale":
            sx = vals[0]
            sy = vals[1] if len(vals) > 1 else sx
            t = t.scale(sx, sy)
        elif name == "rotate" and vals:
            angle = vals[0]
            cx = vals[1] if len(vals) > 1 else 0
            cy = vals[2] if len(vals) > 2 else 0
            t = t.rotate_deg_around(cx, cy, angle)
    return t


def iter_paths_with_groups(element, group_stack=None):
    """Depth-first traversal that yields paths with their group trail."""
    if group_stack is None:
        group_stack = []

    for child in element:
        if child.tag == f"{SVG_TAG}g":
            label = child.attrib.get("inkscape:label") or child.attrib.get("id")
            group_stack.append(label)
            yield from iter_paths_with_groups(child, group_stack)
            group_stack.pop()
        elif child.tag == f"{SVG_TAG}path":
            yield child, [g for g in group_stack if g]


def main():
    tree = ET.parse(SVG_FILE)
    root = tree.getroot()

    view_box = [float(v) for v in root.attrib.get("viewBox", "0 0 1 1").split()]
    _, _, width, height = view_box

    fig, ax = plt.subplots(figsize=(6, 6), dpi=150)

    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")

    for idx, (node, groups) in enumerate(iter_paths_with_groups(root), start=1):
        d = node.attrib.get("d")
        if not d:
            continue

        path = parse_path(d)

        transform = node.attrib.get("transform")
        if transform:
            path = path.transformed(parse_transform(transform))

        # Pick colors from style/fill/stroke
        style = node.attrib.get("style", "")
        fill, stroke, fill_opacity = parse_style(style)
        fill = node.attrib.get("fill", fill) or "none"
        stroke = node.attrib.get("stroke", stroke) or "none"
        facecolor = to_rgba(fill, float(fill_opacity)) if fill != "none" else (0, 0, 0, 0)
        edgecolor = stroke if stroke != "none" else "none"

        xs, ys = path.vertices[:, 0], path.vertices[:, 1]
        min_x, min_y = min(min_x, xs.min()), min(min_y, ys.min())
        max_x, max_y = max(max_x, xs.max()), max(max_y, ys.max())

        group_label = " > ".join(groups) if groups else "(root)"
        print(
            f"[{idx}] id={node.attrib.get('id', '(no id)')}, "
            f"groups={group_label}, fill={fill}, stroke={stroke}, "
            f"opacity={fill_opacity}, transform={transform or 'none'}, "
            f"bbox=({xs.min():.2f},{ys.min():.2f})-({xs.max():.2f},{ys.max():.2f})"
        )

        ax.add_patch(PathPatch(path, facecolor=facecolor, edgecolor=edgecolor, lw=0))

    if all(v != float("inf") for v in (min_x, min_y, max_x, max_y)):
        pad_x = (max_x - min_x) * 0.05 or 1
        pad_y = (max_y - min_y) * 0.05 or 1
        ax.set_xlim(min_x - pad_x, max_x + pad_x)
        ax.set_ylim(max_y + pad_y, min_y - pad_y)  # invert y-axis to match SVG origin
    else:
        ax.set_xlim(0, width)
        ax.set_ylim(height, 0)

    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
