import argparse
import sys
from pathlib import Path

from .info import print_info
from .grid import create_grid_svg
from .render import plot_svg


def build_parser():
    parser = argparse.ArgumentParser(description="Inspect and render SVG paths with Matplotlib.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    info_parser = subparsers.add_parser("info", help="Print SVG metadata (dimensions, viewBox, counts).")
    info_parser.add_argument("svg_file", type=Path, help="Path to the SVG file to inspect.")

    plot_parser = subparsers.add_parser("plot", help="Render the SVG (optionally export to PNG).")
    plot_parser.add_argument("svg_file", type=Path, help="Path to the SVG file to inspect.")
    plot_parser.add_argument("--png", type=Path, dest="png_path", help="Save the rendered output to a PNG file.")
    plot_parser.add_argument("--show", action="store_true", help="Show a window even when saving PNG.")

    grid_parser = subparsers.add_parser("grid", help="Create a new SVG with the source tiled in an NxM grid.")
    grid_parser.add_argument("svg_file", type=Path, help="Path to the source SVG file.")
    grid_parser.add_argument("rows", type=int, help="Number of rows in the grid.")
    grid_parser.add_argument("cols", type=int, help="Number of columns in the grid.")
    grid_parser.add_argument("output", type=Path, help="Output SVG path.")

    return parser


def main(argv=None):
    parser = build_parser()

    argv = sys.argv[1:] if argv is None else argv
    known_commands = {"info", "plot", "grid"}
    if argv and argv[0] not in known_commands.union({"-h", "--help"}):
        argv = ["plot"] + argv

    args = parser.parse_args(argv)
    command = args.command

    svg_file = args.svg_file.expanduser()
    if not svg_file.exists():
        parser.error(f"SVG file not found: {svg_file}")

    if command == "info":
        print_info(svg_file)
    elif command == "grid":
        out_path = getattr(args, "output")
        create_grid_svg(svg_file, rows=args.rows, cols=args.cols, out_path=out_path)
        print(f"Wrote tiled SVG to {out_path}")
    else:
        out_path = getattr(args, "png_path", None)
        show = args.show or out_path is None
        plot_svg(svg_file, out_path=out_path, show=show)


if __name__ == "__main__":
    main()
