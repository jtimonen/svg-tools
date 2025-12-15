import argparse
import sys
from pathlib import Path

from .info import print_info
from .render import plot_svg


def build_parser():
    parser = argparse.ArgumentParser(description="Inspect and render SVG paths with Matplotlib.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    info_parser = subparsers.add_parser("info", help="Print SVG metadata (dimensions, viewBox, counts).")
    info_parser.add_argument("svg_file", type=Path, help="Path to the SVG file to inspect.")

    plot_parser = subparsers.add_parser("plot", help="Render the SVG and log paths.")
    plot_parser.add_argument("svg_file", type=Path, help="Path to the SVG file to inspect.")

    return parser


def main(argv=None):
    parser = build_parser()

    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] not in {"info", "plot", "-h", "--help"}:
        argv = ["plot"] + argv

    args = parser.parse_args(argv)
    command = args.command

    svg_file = args.svg_file.expanduser()
    if not svg_file.exists():
        parser.error(f"SVG file not found: {svg_file}")

    if command == "info":
        print_info(svg_file)
    else:
        plot_svg(svg_file)


if __name__ == "__main__":
    main()
