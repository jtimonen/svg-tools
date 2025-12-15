from pathlib import Path
from typing import Optional
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from matplotlib.patches import PathPatch
from svgpath2mpl import parse_path

from .svg import (
    iter_paths_with_groups,
    matrix_to_affine,
    parse_style,
    parse_viewbox,
    to_float,
)


def plot_svg(svg_path: Path, out_path: Optional[Path] = None, show: bool = True):
    tree = ET.parse(svg_path)
    root = tree.getroot()

    view_box = parse_viewbox(root)
    _, _, width, height = view_box

    fig, ax = plt.subplots(figsize=(6, 6), dpi=150)
    ax.set_facecolor("none")
    fig.patch.set_alpha(0)

    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")

    for node, groups, transform_matrix in iter_paths_with_groups(root):
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

        ax.add_patch(
            PathPatch(
                path,
                facecolor=facecolor,
                edgecolor=edgecolor,
                lw=linewidth,
            )
        )

    if out_path:
        # Preserve full viewBox when exporting so the canvas matches original dimensions.
        ax.set_xlim(0, width)
        ax.set_ylim(height, 0)  # invert y-axis to match SVG origin
    else:
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

    if out_path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_path, bbox_inches=None, transparent=True, facecolor="none")
    if show:
        plt.show()
    plt.close(fig)
