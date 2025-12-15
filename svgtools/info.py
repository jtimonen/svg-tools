from pathlib import Path
import xml.etree.ElementTree as ET

from .svg import iter_paths_with_groups, parse_length, parse_viewbox


def collect_info(svg_path: Path):
    tree = ET.parse(svg_path)
    root = tree.getroot()

    view_box = parse_viewbox(root)
    path_count = 0
    groups = set()
    ids = set()
    for node, group_trail, _ in iter_paths_with_groups(root):
        path_count += 1
        groups.update(g for g in group_trail if g)
        node_id = node.attrib.get("id")
        if node_id:
            ids.add(node_id)

    width_attr = root.attrib.get("width", "(unset)")
    height_attr = root.attrib.get("height", "(unset)")
    parsed_width = parse_length(width_attr if width_attr != "(unset)" else None, None)
    parsed_height = parse_length(height_attr if height_attr != "(unset)" else None, None)
    return {
        "file": svg_path,
        "width_attr": width_attr,
        "height_attr": height_attr,
        "parsed_width": parsed_width,
        "parsed_height": parsed_height,
        "view_box": view_box,
        "paths": path_count,
        "groups": len(groups),
        "ids": len(ids),
    }


def print_info(svg_path: Path):
    info = collect_info(svg_path)
    print(f"File: {info['file']}")
    print(f"Size attrs: width={info['width_attr']}, height={info['height_attr']} (parsed: {info['parsed_width']} x {info['parsed_height']})")
    print(f"ViewBox: {info['view_box']}")
    print(f"Paths: {info['paths']}")
    print(f"Groups: {info['groups']}")
    if info["ids"]:
        print(f"IDs: {info['ids']} unique")
    print("Done.")
