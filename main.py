import argparse
import math
import re
from pathlib import Path
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.patches import PathPatch
from matplotlib.transforms import Affine2D
from svgpath2mpl import parse_path


NS = {"svg": "http://www.w3.org/2000/svg"}
SVG_TAG = f"{{{NS['svg']}}}"
IDENTITY_MATRIX = [
    [1.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0],
]


def parse_style(style_str):
    """Return style key/value pairs parsed from a style string."""
    style = {}
    for kv in style_str.split(";"):
        if ":" in kv:
            k, v = kv.split(":", 1)
            style[k.strip()] = v.strip()
    return style


def to_float(val, default):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def parse_transform_matrix(transform_str):
    """Convert an SVG transform attribute into a 3x3 matrix (list of lists)."""
    matrix = IDENTITY_MATRIX
    for name, args in re.findall(r"([a-zA-Z]+)\(([^)]*)\)", transform_str or ""):
        vals = [to_float(v, 0.0) for v in re.split(r"[ ,]+", args.strip()) if v]
        if name == "matrix" and len(vals) == 6:
            t = [
                [vals[0], vals[2], vals[4]],
                [vals[1], vals[3], vals[5]],
                [0.0, 0.0, 1.0],
            ]
        elif name == "translate":
            tx = vals[0] if vals else 0.0
            ty = vals[1] if len(vals) > 1 else 0.0
            t = [
                [1.0, 0.0, tx],
                [0.0, 1.0, ty],
                [0.0, 0.0, 1.0],
            ]
        elif name == "scale":
            sx = vals[0] if vals else 1.0
            sy = vals[1] if len(vals) > 1 else sx
            t = [
                [sx, 0.0, 0.0],
                [0.0, sy, 0.0],
                [0.0, 0.0, 1.0],
            ]
        elif name == "rotate" and vals:
            angle_rad = math.radians(vals[0])
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            cx = vals[1] if len(vals) > 1 else 0.0
            cy = vals[2] if len(vals) > 2 else 0.0
            # Rotation around (cx, cy): T(cx, cy) * R(angle) * T(-cx, -cy)
            t = [
                [cos_a, -sin_a, cx - cx * cos_a + cy * sin_a],
                [sin_a, cos_a, cy - cx * sin_a - cy * cos_a],
                [0.0, 0.0, 1.0],
            ]
        else:
            continue
        matrix = mat_mul(matrix, t)
    return matrix


def mat_mul(a, b):
    """Multiply two 3x3 matrices represented as lists."""
    return [
        [
            a[0][0] * b[0][0] + a[0][1] * b[1][0] + a[0][2] * b[2][0],
            a[0][0] * b[0][1] + a[0][1] * b[1][1] + a[0][2] * b[2][1],
            a[0][0] * b[0][2] + a[0][1] * b[1][2] + a[0][2] * b[2][2],
        ],
        [
            a[1][0] * b[0][0] + a[1][1] * b[1][0] + a[1][2] * b[2][0],
            a[1][0] * b[0][1] + a[1][1] * b[1][1] + a[1][2] * b[2][1],
            a[1][0] * b[0][2] + a[1][1] * b[1][2] + a[1][2] * b[2][2],
        ],
        [
            a[2][0] * b[0][0] + a[2][1] * b[1][0] + a[2][2] * b[2][0],
            a[2][0] * b[0][1] + a[2][1] * b[1][1] + a[2][2] * b[2][1],
            a[2][0] * b[0][2] + a[2][1] * b[1][2] + a[2][2] * b[2][2],
        ],
    ]


def matrix_to_affine(matrix):
    t = Affine2D()
    t.set_matrix(matrix)
    return t


def iter_paths_with_groups(element, group_stack=None, transform_matrix=None):
    """Depth-first traversal that yields paths with their group trail and accumulated transform."""
    if group_stack is None:
        group_stack = []
    if transform_matrix is None:
        transform_matrix = IDENTITY_MATRIX

    for child in element:
        if child.tag == f"{SVG_TAG}g":
            label = child.attrib.get("inkscape:label") or child.attrib.get("id")
            child_transform = transform_matrix
            if "transform" in child.attrib:
                child_transform = mat_mul(transform_matrix, parse_transform_matrix(child.attrib["transform"]))
            group_stack.append(label)
            yield from iter_paths_with_groups(child, group_stack, child_transform)
            group_stack.pop()
        elif child.tag == f"{SVG_TAG}path":
            path_transform = transform_matrix
            if "transform" in child.attrib:
                path_transform = mat_mul(transform_matrix, parse_transform_matrix(child.attrib["transform"]))
            yield child, [g for g in group_stack if g], path_transform


def main(svg_path: Path):
    tree = ET.parse(svg_path)
    root = tree.getroot()

    view_box = [float(v) for v in root.attrib.get("viewBox", "0 0 1 1").split()]
    _, _, width, height = view_box

    fig, ax = plt.subplots(figsize=(6, 6), dpi=150)

    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")

    for idx, (node, groups, transform_matrix) in enumerate(iter_paths_with_groups(root), start=1):
        d = node.attrib.get("d")
        if not d:
            continue

        path = parse_path(d)

        if transform_matrix:
            path = path.transformed(matrix_to_affine(transform_matrix))

        # Pick colors from style/fill/stroke
        style = node.attrib.get("style", "")
        style_map = parse_style(style)

        fill = node.attrib.get("fill", style_map.get("fill")) or "none"
        stroke = node.attrib.get("stroke", style_map.get("stroke")) or "none"
        fill_opacity = to_float(node.attrib.get("fill-opacity", style_map.get("fill-opacity")), 1.0)
        stroke_opacity = to_float(node.attrib.get("stroke-opacity", style_map.get("stroke-opacity")), 1.0)
        stroke_width = to_float(node.attrib.get("stroke-width", style_map.get("stroke-width")), 1.0)

        facecolor = to_rgba(fill, float(fill_opacity)) if fill != "none" else (0, 0, 0, 0)
        edgecolor = to_rgba(stroke, float(stroke_opacity)) if stroke != "none" else "none"
        linewidth = stroke_width if stroke != "none" else 0

        xs, ys = path.vertices[:, 0], path.vertices[:, 1]
        min_x, min_y = min(min_x, xs.min()), min(min_y, ys.min())
        max_x, max_y = max(max_x, xs.max()), max(max_y, ys.max())

        group_label = " > ".join(groups) if groups else "(root)"
        print(
            f"[{idx}] id={node.attrib.get('id', '(no id)')}, "
            f"groups={group_label}, fill={fill}, stroke={stroke}, "
            f"stroke_width={stroke_width}, opacity=(fill:{fill_opacity}, stroke:{stroke_opacity}), "
            f"transform_matrix={transform_matrix}, "
            f"bbox=({xs.min():.2f},{ys.min():.2f})-({xs.max():.2f},{ys.max():.2f})"
        )

        ax.add_patch(
            PathPatch(
                path,
                facecolor=facecolor,
                edgecolor=edgecolor,
                lw=linewidth,
            )
        )

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
    parser = argparse.ArgumentParser(description="Inspect and render SVG paths with Matplotlib.")
    parser.add_argument("svg_file", type=Path, help="Path to the SVG file to inspect.")
    args = parser.parse_args()

    svg_file = args.svg_file.expanduser()
    if not svg_file.exists():
        parser.error(f"SVG file not found: {svg_file}")

    main(svg_file)
