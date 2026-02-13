#!/usr/bin/env python3
"""Create a periodic-table heatmap from an XYZ file and save it as PNG/HTML.

Examples:
  python xyz_to_periodic_table.py input.xyz output.png
  python xyz_to_periodic_table.py input.xyz output.html
  python xyz_to_periodic_table.py traj.xyz output.png --frame all --dpi 300
  python xyz_to_periodic_table.py traj.extxyz output.png --frame all --unique-structure
"""

from __future__ import annotations

import argparse
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
from bokeh.io.export import export_png
from periodic_trends import plotter


def parse_frame_option(frame_option: str) -> str | int:
    if frame_option.lower() == "all":
        return ":"
    try:
        return int(frame_option)
    except ValueError as exc:
        raise ValueError("--frame must be an integer or 'all'.") from exc


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
    xyz_path: Path, frame_option: str, unique_structure: bool = False
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

    counts: Counter[str] = Counter()
    for atoms in frames:
        counts.update(atoms.get_chemical_symbols())

    if not counts:
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


def export_periodic_plot(
    df: pd.DataFrame, output_path: Path, title: str | None, dpi: int
) -> None:
    suffix = output_path.suffix.lower()
    if suffix == ".html":
        plotter(
            df,
            "Element",
            "element_count",
            show=False,
            output_filename=str(output_path),
            cbar_title="Count",
            title=title,
        )
        return

    if suffix != ".png":
        raise ValueError("Output extension must be .png or .html")

    fig = plotter(
        df,
        "Element",
        "element_count",
        show=False,
        cbar_title="Count",
        title=title,
    )

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
        description="Read an XYZ file, count elements, and plot them on a periodic table.",
    )
    parser.add_argument("xyz", type=Path, help="Input .xyz file")
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
        "--dpi",
        type=int,
        default=300,
        help="PNG DPI (used to compute render scale factor, default: 300).",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        if not args.xyz.exists():
            raise ValueError(f"Input file not found: {args.xyz}")

        counts, total_frames, selected_frames = element_counts_from_xyz(
            args.xyz,
            args.frame,
            unique_structure=args.unique_structure,
        )
        df = counts_to_dataframe(counts)

        export_periodic_plot(df, args.output, title=args.title, dpi=args.dpi)

        if args.save_html is not None:
            export_periodic_plot(df, args.save_html, title=args.title, dpi=args.dpi)

        if args.unique_structure:
            print(
                "Frames counted: "
                f"{selected_frames}/{total_frames} (unique info['structure_name'])"
            )

        print("Element counts:")
        for element, n in sorted(
            counts.items(), key=lambda x: atomic_numbers.get(x[0], 999)
        ):
            print(f"  {element}: {n}")

        print(f"Saved: {args.output}")
        if args.save_html is not None:
            print(f"Saved: {args.save_html}")

        return 0
    except Exception as exc:
        raise SystemExit(f"Error: {exc}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
