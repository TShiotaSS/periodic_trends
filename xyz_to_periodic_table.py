#!/usr/bin/env python3
"""Create a periodic-table heatmap from XYZ/CSV data and save it as PNG/HTML.

Examples:
  python xyz_to_periodic_table.py input.xyz output.png
  python xyz_to_periodic_table.py input.xyz output.html
  python xyz_to_periodic_table.py input_counts.csv output.html
  python xyz_to_periodic_table.py input.xyz output.html --fraction
  python xyz_to_periodic_table.py input.xyz output.html --fraction --log-fraction
  python xyz_to_periodic_table.py traj.xyz output.png --frame all --dpi 300
  python xyz_to_periodic_table.py traj.xyz output.png --cmap viridis
  python xyz_to_periodic_table.py traj.xyz output.html --color-min 0 --color-max 20
  python xyz_to_periodic_table.py traj.xyz output.html --print-data
  python xyz_to_periodic_table.py traj.xyz output.html --all-black-text
  python xyz_to_periodic_table.py traj.extxyz output.png --frame all --unique-structure
  python xyz_to_periodic_table.py traj.extxyz output.html --log-scale
  python xyz_to_periodic_table.py traj.extxyz output.html --exclude-elements H O
"""

from __future__ import annotations

import argparse
import math
import os
import tempfile
from collections import Counter
from pathlib import Path

# Avoid matplotlib cache warnings in environments where ~/.matplotlib is not writable.
_mpl_config = Path(tempfile.gettempdir()) / "matplotlib"
_mpl_config.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_mpl_config))

import pandas as pd
from ase.data import atomic_numbers
from ase.io import read
from bokeh.io import output_file, save
from bokeh.io.export import export_png
from matplotlib import colormaps
from periodic_trends import plotter


def parse_frame_option(frame_option: str) -> str | int:
    if frame_option.lower() == "all":
        return ":"
    try:
        return int(frame_option)
    except ValueError as exc:
        raise ValueError("--frame must be an integer or 'all'.") from exc


def parse_exclude_elements(raw_values: list[str] | None) -> list[str]:
    if not raw_values:
        return []

    parsed: list[str] = []
    seen: set[str] = set()
    for raw in raw_values:
        for token in raw.split(","):
            symbol = token.strip()
            if not symbol:
                continue
            normalized = normalize_element_symbol(symbol)
            if normalized in seen:
                continue
            seen.add(normalized)
            parsed.append(normalized)
    return parsed


def normalize_element_symbol(symbol: str) -> str:
    cleaned = symbol.strip()
    if not cleaned:
        raise ValueError("Element symbol cannot be empty.")

    normalized = cleaned[0].upper() + cleaned[1:].lower()
    if normalized not in atomic_numbers:
        raise ValueError(f"Invalid element symbol: {symbol}")
    return normalized


def resolve_cmap(cmap_name: str):
    normalized = cmap_name.strip()
    if not normalized:
        raise ValueError("--cmap must be a non-empty colormap name.")

    try:
        return colormaps[normalized]
    except Exception as exc:
        raise ValueError(
            f"Unknown colormap for --cmap: {normalized}. "
            "Try common options like: plasma, viridis, inferno, magma, cividis."
        ) from exc


def default_csv_output_path(
    output_path: Path, fraction_mode: bool, log_fraction_mode: bool
) -> Path:
    stemmed = output_path.with_suffix("")
    if log_fraction_mode:
        suffix = "_fraction_log.csv"
    elif fraction_mode:
        suffix = "_fraction.csv"
    else:
        suffix = "_counts.csv"
    return stemmed.parent / f"{stemmed.name}{suffix}"


def unique_frames_by_structure_name(frames: list, xyz_path: Path) -> list:
    seen_structure_names: set[str] = set()
    unique_frames: list = []
    missing_name_indices: list[int] = []

    for idx, atoms in enumerate(frames):
        structure_name = atoms.info.get("structure_name")
        if structure_name is None or str(structure_name).strip() == "":
            missing_name_indices.append(idx)
            continue

        key = str(structure_name)
        if key in seen_structure_names:
            continue

        seen_structure_names.add(key)
        unique_frames.append(atoms)

    if missing_name_indices:
        preview = ", ".join(str(i) for i in missing_name_indices[:10])
        suffix = " ..." if len(missing_name_indices) > 10 else ""
        raise ValueError(
            "--unique-structure requires non-empty info['structure_name'] in every frame. "
            f"Missing at frame indices: {preview}{suffix} (file: {xyz_path})."
        )

    return unique_frames


def element_counts_from_xyz(
    xyz_path: Path,
    frame_option: str,
    unique_structure: bool = False,
    exclude_elements: list[str] | None = None,
) -> tuple[Counter[str], int, int]:
    index = parse_frame_option(frame_option)
    atoms_or_list = read(str(xyz_path), index=index)

    if isinstance(atoms_or_list, list):
        frames = atoms_or_list
    else:
        frames = [atoms_or_list]

    total_frames = len(frames)

    if unique_structure and total_frames > 1:
        frames = unique_frames_by_structure_name(frames, xyz_path)

    selected_frames = len(frames)

    exclude_set = set(exclude_elements or [])
    counts: Counter[str] = Counter()
    for atoms in frames:
        counts.update(sym for sym in atoms.get_chemical_symbols() if sym not in exclude_set)

    if not counts:
        if exclude_set:
            excluded = ", ".join(sorted(exclude_set, key=lambda e: atomic_numbers[e]))
            raise ValueError(
                f"No atoms left after excluding elements ({excluded}) in '{xyz_path}'."
            )
        raise ValueError(f"No atoms found in '{xyz_path}'.")

    return counts, total_frames, selected_frames


def counts_to_dataframe(counts: Counter[str]) -> pd.DataFrame:
    elements = sorted(counts.keys(), key=lambda e: atomic_numbers.get(e, 999))
    return pd.DataFrame(
        {
            "Element": elements,
            "element_count": [counts[e] for e in elements],
        }
    )


def build_plot_and_csv_data(
    counts: Counter[str], fraction_mode: bool, log_fraction_mode: bool
) -> tuple[pd.DataFrame, pd.DataFrame, str, str, int]:
    counts_df = counts_to_dataframe(counts)

    if not fraction_mode:
        return counts_df, counts_df.copy(), "element_count", "Count", 0

    max_count = counts_df["element_count"].max()
    if max_count <= 0:
        raise ValueError("Cannot compute fractions because max element count is not positive.")

    fractions = counts_df["element_count"] / max_count
    fraction_df = counts_df.copy()
    fraction_df["element_fraction"] = fractions

    if log_fraction_mode:
        if (fraction_df["element_fraction"] <= 0).any():
            raise ValueError(
                "Cannot compute log-fraction because some element fractions are <= 0."
            )
        fraction_df["element_fraction_log10"] = fraction_df["element_fraction"].map(
            lambda x: math.log10(x)
        )
        plot_df = fraction_df[["Element", "element_fraction_log10"]].copy()
        csv_df = fraction_df[
            ["Element", "element_count", "element_fraction", "element_fraction_log10"]
        ].copy()
        return plot_df, csv_df, "element_fraction_log10", "log(Element fraction)", 3

    plot_df = fraction_df[["Element", "element_fraction"]].copy()
    csv_df = fraction_df[["Element", "element_count", "element_fraction"]].copy()

    return plot_df, csv_df, "element_fraction", "Element fraction", 3


def element_counts_from_csv(
    csv_path: Path, exclude_elements: list[str] | None = None
) -> Counter[str]:
    try:
        raw_df = pd.read_csv(csv_path)
    except Exception as exc:
        raise ValueError(f"Failed to read CSV input: {csv_path}") from exc

    if raw_df.empty:
        raise ValueError(f"CSV input has no rows: {csv_path}")

    if {"Element", "element_count"}.issubset(raw_df.columns):
        df = raw_df[["Element", "element_count"]].copy()
    elif len(raw_df.columns) >= 2:
        df = raw_df.iloc[:, :2].copy()
        df.columns = ["Element", "element_count"]
    else:
        raise ValueError(
            "CSV input must contain 'Element' and 'element_count' columns "
            "or at least two columns."
        )

    df = df.dropna(subset=["Element", "element_count"]).copy()
    if df.empty:
        raise ValueError(f"CSV input has no valid Element/count rows: {csv_path}")

    df["Element"] = df["Element"].astype(str).map(normalize_element_symbol)
    df["element_count"] = pd.to_numeric(df["element_count"], errors="raise")

    if (df["element_count"] < 0).any():
        raise ValueError(f"CSV input contains negative counts: {csv_path}")

    non_integer_mask = ~df["element_count"].map(lambda x: float(x).is_integer())
    if non_integer_mask.any():
        raise ValueError(f"CSV input contains non-integer counts: {csv_path}")

    df["element_count"] = df["element_count"].astype(int)

    exclude_set = set(exclude_elements or [])
    if exclude_set:
        df = df[~df["Element"].isin(exclude_set)].copy()

    if df.empty:
        if exclude_set:
            excluded = ", ".join(sorted(exclude_set, key=lambda e: atomic_numbers[e]))
            raise ValueError(
                f"No counts left after excluding elements ({excluded}) in '{csv_path}'."
            )
        raise ValueError(f"No counts left after filtering CSV input: {csv_path}")

    grouped = (
        df.groupby("Element", as_index=False)["element_count"]
        .sum()
        .sort_values("Element", key=lambda s: s.map(lambda e: atomic_numbers.get(e, 999)))
    )

    return Counter(dict(zip(grouped["Element"], grouped["element_count"], strict=False)))


def export_counts_csv(df: pd.DataFrame, csv_path: Path) -> None:
    df.to_csv(csv_path, index=False)


def export_periodic_plot(
    df: pd.DataFrame,
    output_path: Path,
    title: str | None,
    dpi: int,
    log_scale: bool,
    exclude_elements: list[str],
    cmap,
    print_data: bool,
    all_black_text: bool,
    color_min: float | None,
    color_max: float | None,
    column_data: str,
    cbar_title: str,
    float_decimals: int,
) -> None:
    def apply_colorbar_title_style(fig) -> None:
        colorbar_title_size = "16pt"
        for layout_name in ("left", "right", "above", "below", "center"):
            layouts = getattr(fig, layout_name, None)
            if not layouts:
                continue
            for item in layouts:
                if item.__class__.__name__ != "ColorBar":
                    continue
                if hasattr(item, "title_text_font_style"):
                    item.title_text_font_style = "normal"
                if hasattr(item, "title_text_font_size"):
                    item.title_text_font_size = colorbar_title_size

    def text_color_for_fill(hex_color: str) -> str:
        if not isinstance(hex_color, str):
            return "#000000"
        color = hex_color.strip()
        if not color.startswith("#"):
            return "#000000"
        color = color[1:]
        if len(color) == 3:
            color = "".join(ch * 2 for ch in color)
        if len(color) != 6:
            return "#000000"

        try:
            r = int(color[0:2], 16) / 255.0
            g = int(color[2:4], 16) / 255.0
            b = int(color[4:6], 16) / 255.0
        except ValueError:
            return "#000000"

        def srgb_to_linear(x: float) -> float:
            return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4

        luminance = (
            0.2126 * srgb_to_linear(r)
            + 0.7152 * srgb_to_linear(g)
            + 0.0722 * srgb_to_linear(b)
        )
        return "#FFFFFF" if luminance < 0.45 else "#000000"

    def apply_adaptive_text_colors(fig, force_black_text: bool = False) -> None:
        target_sources = []
        for renderer in fig.renderers:
            source = getattr(renderer, "data_source", None)
            if source is None:
                continue
            if "sym" in source.data and "type_color" in source.data:
                if force_black_text:
                    source.data["text_color"] = ["#000000"] * len(source.data["sym"])
                else:
                    fill_colors = list(source.data["type_color"])
                    source.data["text_color"] = [text_color_for_fill(c) for c in fill_colors]
                target_sources.append(source)

        if not target_sources:
            return

        for renderer in fig.renderers:
            source = getattr(renderer, "data_source", None)
            if source is None or "text_color" not in source.data:
                continue

            for glyph_attr in (
                "glyph",
                "nonselection_glyph",
                "muted_glyph",
                "selection_glyph",
                "hover_glyph",
            ):
                glyph = getattr(renderer, glyph_attr, None)
                if glyph is not None and hasattr(glyph, "text_color"):
                    glyph.text_color = "text_color"

    def hide_nan_data_labels(fig) -> None:
        for renderer in fig.renderers:
            source = getattr(renderer, "data_source", None)
            if source is None or "data_text" not in source.data:
                continue

            cleaned = []
            for value in list(source.data["data_text"]):
                if isinstance(value, str) and value.strip().lower() == "nan":
                    cleaned.append("")
                elif isinstance(value, float) and math.isnan(value):
                    cleaned.append("")
                else:
                    cleaned.append(value)
            source.data["data_text"] = cleaned

    def apply_excluded_borders(fig, excluded: list[str]) -> None:
        if not excluded:
            return

        excluded_set = set(excluded)
        for renderer in fig.renderers:
            source = getattr(renderer, "data_source", None)
            glyph = getattr(renderer, "glyph", None)
            if source is None or glyph is None:
                continue
            if "sym" not in source.data or "type_color" not in source.data:
                continue

            symbols = list(source.data["sym"])
            line_colors = ["#000000"] * len(symbols)
            line_alphas = [1.0 if sym in excluded_set else 0.0 for sym in symbols]

            source.data["line_color"] = line_colors
            source.data["line_alpha"] = line_alphas
            glyph.line_color = "line_color"
            glyph.line_alpha = "line_alpha"
            glyph.line_width = 1.25
            return

    special_elements = exclude_elements if exclude_elements else None
    suffix = output_path.suffix.lower()
    if suffix == ".html":
        fig = plotter(
            df,
            "Element",
            column_data,
            show=False,
            cmap=cmap,
            log_scale=log_scale,
            print_data=print_data,
            float_decimals=float_decimals,
            color_min=color_min,
            color_max=color_max,
            special_elements=special_elements,
            special_color="#FFFFFF",
            cbar_title=cbar_title,
            title=title,
        )
        apply_excluded_borders(fig, exclude_elements)
        apply_adaptive_text_colors(fig, force_black_text=all_black_text)
        apply_colorbar_title_style(fig)
        hide_nan_data_labels(fig)
        output_file(str(output_path))
        save(fig)
        return

    if suffix != ".png":
        raise ValueError("Output extension must be .png or .html")

    fig = plotter(
        df,
        "Element",
        column_data,
        show=False,
        cmap=cmap,
        log_scale=log_scale,
        print_data=print_data,
        float_decimals=float_decimals,
        color_min=color_min,
        color_max=color_max,
        special_elements=special_elements,
        special_color="#FFFFFF",
        cbar_title=cbar_title,
        title=title,
    )
    apply_excluded_borders(fig, exclude_elements)
    apply_adaptive_text_colors(fig, force_black_text=all_black_text)
    apply_colorbar_title_style(fig)
    hide_nan_data_labels(fig)

    if dpi <= 0:
        raise ValueError("--dpi must be a positive integer.")

    # Bokeh renderers are CSS-pixel based; 96 dpi is the browser baseline.
    scale_factor = dpi / 96.0
    try:
        export_png(fig, filename=str(output_path), scale_factor=scale_factor)
    except Exception as exc:
        raise RuntimeError(
            "Failed to render PNG because Bokeh image export is unavailable. "
            "Install runtime dependencies, for example:\n"
            "  pip install selenium\n"
            "and install a browser + driver (chromium/chromedriver or firefox/geckodriver)."
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read XYZ/CSV data, count elements, and plot them on a periodic table.",
    )
    parser.add_argument(
        "input_data",
        type=Path,
        help="Input file (.xyz/.extxyz or .csv with Element/element_count columns)",
    )
    parser.add_argument("output", type=Path, help="Output file (.png or .html)")
    parser.add_argument(
        "--frame",
        default="all",
        help="Frame index for trajectory-like XYZ files (integer) or 'all' (default).",
    )
    parser.add_argument(
        "--unique-structure",
        action="store_true",
        help=(
            "For multi-frame inputs, count only the first frame per unique "
            "info['structure_name']."
        ),
    )
    parser.add_argument(
        "--title",
        default="Element Counts",
        help="Plot title (default: 'Element Counts').",
    )
    parser.add_argument(
        "--save-html",
        type=Path,
        default=None,
        help="Optionally save interactive HTML alongside main output.",
    )
    parser.add_argument(
        "--save-csv",
        type=Path,
        default=None,
        help=(
            "Path for CSV export of element counts. "
            "Default: <output_stem>_counts.csv, "
            "<output_stem>_fraction.csv with --fraction, "
            "or <output_stem>_fraction_log.csv with --fraction --log-fraction."
        ),
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="PNG DPI (used to compute render scale factor, default: 300).",
    )
    parser.add_argument(
        "--log-scale",
        action="store_true",
        help="Use logarithmic scale for the colorbar values.",
    )
    parser.add_argument(
        "--exclude-elements",
        nargs="+",
        default=None,
        help=(
            "Exclude element symbols from counting and render them in white with black borders. "
            "Examples: --exclude-elements H O or --exclude-elements H,O"
        ),
    )
    parser.add_argument(
        "--print-data",
        action="store_true",
        help="Print element counts as text labels inside periodic-table cells.",
    )
    parser.add_argument(
        "--all-black-text",
        action="store_true",
        help="Render all text labels in black (disable adaptive black/white text colors).",
    )
    parser.add_argument(
        "--fraction",
        action="store_true",
        help=(
            "Visualize element fractions normalized by the maximum element count "
            "(fraction = count / max_count)."
        ),
    )
    parser.add_argument(
        "--log-fraction",
        action="store_true",
        help=(
            "Visualize log10-transformed element fraction. "
            "Requires --fraction."
        ),
    )
    parser.add_argument(
        "--cmap",
        default="plasma",
        help="Matplotlib colormap name (default: plasma). Example: viridis, cividis, inferno.",
    )
    parser.add_argument(
        "--color-min",
        type=float,
        default=None,
        help="Minimum value for colorbar range (default: data minimum).",
    )
    parser.add_argument(
        "--color-max",
        type=float,
        default=None,
        help="Maximum value for colorbar range (default: data maximum).",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        if not args.input_data.exists():
            raise ValueError(f"Input file not found: {args.input_data}")

        exclude_elements = parse_exclude_elements(args.exclude_elements)
        cmap = resolve_cmap(args.cmap)
        if args.log_fraction and not args.fraction:
            raise ValueError("--log-fraction requires --fraction.")
        if args.log_fraction and args.log_scale:
            raise ValueError(
                "--log-fraction cannot be combined with --log-scale. "
                "Use one log transform at a time."
            )
        if (
            args.color_min is not None
            and args.color_max is not None
            and args.color_min >= args.color_max
        ):
            raise ValueError("--color-min must be smaller than --color-max.")

        is_csv_input = args.input_data.suffix.lower() == ".csv"
        if is_csv_input:
            if args.unique_structure:
                raise ValueError("--unique-structure can only be used with XYZ/EXTXYZ input.")
            if args.frame != "all":
                raise ValueError("--frame can only be used with XYZ/EXTXYZ input.")
            counts = element_counts_from_csv(
                args.input_data,
                exclude_elements=exclude_elements,
            )
            total_frames = None
            selected_frames = None
        else:
            counts, total_frames, selected_frames = element_counts_from_xyz(
                args.input_data,
                args.frame,
                unique_structure=args.unique_structure,
                exclude_elements=exclude_elements,
            )
        plot_df, csv_df, column_data, cbar_title, float_decimals = build_plot_and_csv_data(
            counts, fraction_mode=args.fraction, log_fraction_mode=args.log_fraction
        )

        csv_output_path = args.save_csv or default_csv_output_path(
            args.output, fraction_mode=args.fraction, log_fraction_mode=args.log_fraction
        )
        export_counts_csv(csv_df, csv_output_path)

        export_periodic_plot(
            plot_df,
            args.output,
            title=args.title,
            dpi=args.dpi,
            log_scale=args.log_scale,
            exclude_elements=exclude_elements,
            cmap=cmap,
            print_data=args.print_data,
            all_black_text=args.all_black_text,
            color_min=args.color_min,
            color_max=args.color_max,
            column_data=column_data,
            cbar_title=cbar_title,
            float_decimals=float_decimals,
        )

        if args.save_html is not None:
            export_periodic_plot(
                plot_df,
                args.save_html,
                title=args.title,
                dpi=args.dpi,
                log_scale=args.log_scale,
                exclude_elements=exclude_elements,
                cmap=cmap,
                print_data=args.print_data,
                all_black_text=args.all_black_text,
                color_min=args.color_min,
                color_max=args.color_max,
                column_data=column_data,
                cbar_title=cbar_title,
                float_decimals=float_decimals,
            )

        if args.unique_structure:
            print(
                "Frames counted: "
                f"{selected_frames}/{total_frames} (unique info['structure_name'])"
            )
        elif total_frames is not None and selected_frames is not None:
            print(f"Frames counted: {selected_frames}/{total_frames}")
        else:
            print("Frames counted: N/A (CSV input)")
        if total_frames is None:
            print("Total frames in input: N/A (CSV input)")
        else:
            print(f"Total frames in input: {total_frames}")
        if args.log_fraction:
            print(
                "Visualization mode: log(Element fraction) "
                "(Element fraction = count / max_count)"
            )
        elif args.fraction:
            print("Visualization mode: Element fraction (count / max_count)")
        if exclude_elements:
            print(f"Excluded elements (white + black border): {', '.join(exclude_elements)}")

        print("Element counts:")
        for element, n in sorted(
            counts.items(), key=lambda x: atomic_numbers.get(x[0], 999)
        ):
            print(f"  {element}: {n}")

        print(f"Saved: {args.output}")
        if args.save_html is not None:
            print(f"Saved: {args.save_html}")
        print(f"Saved: {csv_output_path}")

        return 0
    except Exception as exc:
        raise SystemExit(f"Error: {exc}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
