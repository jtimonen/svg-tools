# svg-tools

svg-tools is a simple viewer/debugger/animator for vector graphics assets. It walks the paths in an SVG, prints grouping/transform info, and renders shapes with Matplotlib for quick inspection.

## Requirements
- Python 3.9+
- Dependencies: `matplotlib`, `svgpath2mpl`

Install deps:
```bash
python -m pip install -r requirements.txt
```

## Usage
CLI commands (Windows users can run `svgtools.bat`):
```bash
svgtools plot path/to/your.svg   # render + log paths (default if no subcommand)
svgtools info path/to/your.svg   # print metadata only

# alternative without adding to PATH
python -m svgtools plot path/to/your.svg
```
The tool logs each path with its group trail, fill/stroke/opacity, transform, and bounding box, then renders the composed graphic in a Matplotlib window when using `plot`.

## Notes
- SVG transforms (matrix/translate/scale/rotate) are applied via Matplotlib `Affine2D`.
- The viewer inverts the y-axis so the plot matches SVG coordinates.
- If your SVG uses other element types (e.g., `<rect>`), convert them to paths or extend the parser.
