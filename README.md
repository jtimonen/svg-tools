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
svgtools grid path/to/your.svg 2 3 out.svg  # tile source in a 2x3 grid and save
svgtools move grid.svg 405 0 0 1 2 out.svg  # copy tile (row 0,col 0) to (row 1,col 2)

# alternative without adding to PATH
python -m svgtools plot path/to/your.svg
```
The tool renders the composed graphic in a Matplotlib window when using `plot`. To export directly:
```bash
svgtools plot path/to/your.svg --png out.png    # save PNG at full viewBox size; omit to show window
svgtools plot path/to/your.svg --png out.png --show  # save and also show
```

`grid` uses the original SVG’s full canvas size (width/height + viewBox) for each tile so repeated boxes match the source dimensions.

## Installation / making `svgtools` available anywhere
- Quick PATH add (Windows): add the repo folder to `PATH` so `svgtools.bat` is found, e.g. `C:\Users\Juho\Documents\HobbyProjects\svg-tools`.
- Editable install: run `python -m pip install -e .` in the repo. Make sure your Python Scripts directory is on `PATH` (e.g. `%USERPROFILE%\AppData\Local\Programs\Python\PythonXX\Scripts`), then call `svgtools ...` from anywhere.
- pipx: `pipx install --editable .` to isolate dependencies and still get a global `svgtools` command.

## Notes
- SVG transforms (matrix/translate/scale/rotate) are applied via Matplotlib `Affine2D`.
- The viewer inverts the y-axis so the plot matches SVG coordinates.
- If your SVG uses other element types (e.g., `<rect>`), convert them to paths or extend the parser.
