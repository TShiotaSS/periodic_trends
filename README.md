# Periodic Trend Plotter

Python script to plot periodic trends as a heat map over the periodic table of elements.

## Installation

```
pip install git+https://github.com/Andrew-S-Rosen/periodic_trends.git
```

## Usage

This Python code can be used to plot a heat map over an image of the periodic table of elements for easy and automated visualization of periodic trends.

A minimal example using an [example CSV file](https://github.com/Andrew-S-Rosen/periodic_trends/blob/master/example_data/ionization_energies.csv) is as follows:

```python
from periodic_trends import plotter
import pandas as pd

df = pd.read_csv("ionization_energies.csv", names=["Element", "Ionization Energy"])
plotter(df, "Element", "Ionization Energy")
```

![plot1](example_images/plot1.png)

The `plotter()` function reads a pandas DataFrame containing periodic trend data. DataFrames can be read from a wide range of data formats, such as csv and xlsx. The `plotter()` takes three required arguments, the first being the DataFrame itself, the second is the name of the column containing the atom symbols of your elements, and the last being the name of column of the values you wish to plot.

After the `periodic_trends.py` script is run, it will show the plot in your web browser. To save the image, simply click the save icon that appears in the web browser figure.

There are numerous optional arguments, which can be used to modify the appearance of the figure. A couple of examples using various optional keyword arguments are as follows:

```python
from periodic_trends import plotter
import pandas as pd

df = pd.read_csv("ionization_energies.csv", names=["Element", "Ionization Energy"])
plotter(df, "Element", "Ionization Energy", log_scale=True)
```

![plot2](example_images/plot2.png)

```python
from periodic_trends import plotter
import pandas as pd
from matplotlib import cm

df = pd.read_csv("ionization_energies.csv", names=["Element", "Ionization Energy"])
plotter(
    df,
    "Element",
    "Ionization Energy",
    cmap=cm.viridis,
    alpha=0.7,
    extended=False,
    periods_remove=[1],
)
```

![plot3](example_images/plot3.png)

```python
import pandas as pd
from periodic_trends import plotter
from matplotlib import cm

df = pd.read_csv("ionization_energies.csv", names=["Element", "Ionization Energy"])
test = plotter(df, "Element", "Ionization Energy", print_data=True, cmap=cm.summer)
```

![plot4](example_images/plot4.png)

## XYZ Utility (Element Count)

This fork includes `xyz_to_periodic_table.py`, a utility script that reads `.xyz/.extxyz` files with `ase` (or count CSV files), and visualizes element counts with `periodic_trends`.

Basic examples:

```bash
python xyz_to_periodic_table.py input.xyz output.png --dpi 300
python xyz_to_periodic_table.py input.xyz output.html
python xyz_to_periodic_table.py input_counts.csv output.html
python xyz_to_periodic_table.py input.xyz output.html --fraction
python xyz_to_periodic_table.py input.xyz output.html --fraction --log-fraction
python xyz_to_periodic_table.py input.xyz output.png --cmap viridis
python xyz_to_periodic_table.py input.xyz output.html --blank-color "#e8f0fe"
python xyz_to_periodic_table.py input.xyz output.html --color-min 0 --color-max 20
python xyz_to_periodic_table.py input.xyz output.html --print-data
python xyz_to_periodic_table.py input.xyz output.html --all-black-text
python xyz_to_periodic_table.py input.xyz output.html --highlight-elements Fe O
python xyz_to_periodic_table.py input.xyz output.png --frame 0 --dpi 600
python xyz_to_periodic_table.py input.extxyz output.png --frame all --unique-structure
python xyz_to_periodic_table.py input.extxyz output.html --log-scale
python xyz_to_periodic_table.py input.extxyz output.html --exclude-elements H O
```

Arguments:

- `input_data`: input `.xyz/.extxyz` file, or `.csv` with `Element,element_count`
- `output`: output path (`.png` or `.html`)
- `--frame`: frame index (`0`, `1`, ...) or `all` (default)
- `--unique-structure`: for multi-frame input, count only the first frame for each unique `info['structure_name']`
- `--dpi`: PNG DPI (default: `300`)
- `--cmap`: matplotlib colormap name (default: `plasma`)
- `--blank-color`: fill color for elements without data (default: `#c4c4c4`)
- `--color-min`: minimum value for colorbar range (default: data min)
- `--color-max`: maximum value for colorbar range (default: data max)
- `--log-scale`: use logarithmic scale for colorbar values
- `--exclude-elements`: exclude symbols from counting and render those cells in white with a black border
- `--highlight-elements`: draw fluorescent green borders around selected element symbols
- `--print-data`: print element counts directly in each periodic-table cell
- `--all-black-text`: render included-element text labels in black (no-data labels stay gray)
- `--fraction`: visualize normalized fraction (`count / max_count`) instead of raw count
- `--log-fraction`: visualize `log10(element_fraction)` (requires `--fraction`)
- `--title`: plot title (default: `Element Counts`)
- `--save-html`: optional additional HTML output path
- `--save-csv`: CSV output path override (default: `<output_stem>_counts.csv`, `<output_stem>_fraction.csv` with `--fraction`, `<output_stem>_fraction_log.csv` with `--fraction --log-fraction`)

Notes:

- PNG export uses bokeh image export and requires `selenium` plus a browser/driver pair.
- Internal conversion uses `scale_factor = dpi / 96`.
- `--unique-structure` expects each frame to contain non-empty `info['structure_name']` metadata.
- `--cmap` can use any matplotlib colormap name (for example: `plasma`, `viridis`, `inferno`, `cividis`).
- `--blank-color` accepts valid matplotlib/CSS colors (for example: `#e8f0fe`, `lightgray`).
- `--color-min` and `--color-max` let you align colorbar scales across multiple figures.
- `--fraction` uses `element_fraction = element_count / max(element_count)`.
- `--log-fraction` uses `log10(element_fraction)`.
- `--log-scale` requires strictly positive values (element counts are positive by construction).
- `--log-fraction` and `--log-scale` cannot be combined.
- `--exclude-elements` accepts space-separated or comma-separated symbols (`H O` or `H,O`).
- `--highlight-elements` accepts space-separated or comma-separated symbols (`Fe O` or `Fe,O`).
- If an element is specified in both `--exclude-elements` and `--highlight-elements`, the cell stays white (excluded) and the border uses fluorescent green (highlight takes border priority).
- Text color is automatically switched for readability (`black` on light cells, `white` on dark cells).
- Elements without data are shown with gray text to make non-included cells easier to distinguish.
- `--all-black-text` forces included-element labels to black while keeping no-data labels gray.
- The colorbar title is rendered in a larger non-italic font for readability.
- With `--fraction`, the colorbar title changes to `Element fraction` (otherwise `Count`).
- With `--fraction --log-fraction`, the colorbar title changes to `log(Element fraction)`.
- With `--print-data`, counts are rendered as integers (for example, `3` instead of `3.0`).
- The script always prints frame summary, including total input frame count.
- CSV output is enabled by default; counts/fractions are always written to CSV.
- When input is CSV, the plot is generated directly from that CSV (`Element,element_count`).

## Troubleshooting

If the plot doesn't show up the first time (sometimes happens in Jupyter Notebooks), try calling the following first:

```python
from bokeh.io import output_notebook

output_notebook()
```

## Change History

See `CHANGELOG.md` for modification history in this fork.
