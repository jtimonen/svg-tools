import math
import re
import xml.etree.ElementTree as ET

from matplotlib.transforms import Affine2D

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


def parse_length(val, default):
    if val is None:
        return default
    match = re.match(r"[-+]?[0-9]*\.?[0-9]+", str(val))
    if match:
        return to_float(match.group(), default)
    return default


def parse_viewbox(root: ET.Element):
    view_box = root.attrib.get("viewBox")
    if view_box:
        vals = [to_float(v, 0.0) for v in view_box.split()]
        if len(vals) == 4:
            return vals
    width = parse_length(root.attrib.get("width"), 1.0)
    height = parse_length(root.attrib.get("height"), 1.0)
    return [0.0, 0.0, width, height]


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
