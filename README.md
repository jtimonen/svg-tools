# svg-tools

svg-tools is a simple viewer/debugger/animator for vector graphics assets. It walks the paths in an SVG, prints grouping/transform info, and renders shapes with Matplotlib for quick inspection.

## Requirements
- Python 3.9+
- Dependencies: `matplotlib`, `svgpath2mpl`

Install deps:
```bash
python -m pip install matplotlib svgpath2mpl
```

## Usage
1) Make sure `main.py` points `SVG_FILE` to your SVG (defaults to `../game-art/characters/hero.svg`).
2) Run the script:
```bash
python main.py
```
The script logs each path with its group trail, fill/stroke/opacity, transform, and bounding box, then renders the composed graphic.

## Notes
- SVG transforms (matrix/translate/scale/rotate) are applied via Matplotlib `Affine2D`.
- The viewer inverts the y-axis so the plot matches SVG coordinates.
- If your SVG uses other element types (e.g., `<rect>`), convert them to paths or extend the parser.
