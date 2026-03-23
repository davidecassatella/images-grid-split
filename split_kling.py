#!/usr/bin/env python3
"""
Kling Grid Splitter — CLI unificato per splitting di griglie 2×2 e 3×3.

Uso:
  python split_kling.py 2x2 [-i INPUT] [-o OUTPUT] [-f FILE]
  python split_kling.py 3x3 [-i INPUT] [-o OUTPUT] [-f FILE]
  python split_kling.py ui
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

VALID_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


# ── split logic (senza side-effect di stampa) ──────────────────────────────────


def _do_split_2x2(image_path: Path, output_dir: Path) -> None:
    with Image.open(image_path) as img:
        w, h = img.size
        hw, hh = w // 2, h // 2
        for label, box in [
            ("01_top_left", (0, 0, hw, hh)),
            ("02_top_right", (hw, 0, w, hh)),
            ("03_bottom_left", (0, hh, hw, h)),
            ("04_bottom_right", (hw, hh, w, h)),
        ]:
            img.crop(box).save(output_dir / f"{image_path.stem}_{label}.png")


def _do_split_3x3(image_path: Path, output_dir: Path) -> None:
    with Image.open(image_path) as img:
        w, h = img.size
        cw, ch = w // 3, h // 3
        idx = 1
        for row in range(3):
            for col in range(3):
                left = col * cw
                top = row * ch
                right = w if col == 2 else (col + 1) * cw
                bottom = h if row == 2 else (row + 1) * ch
                img.crop((left, top, right, bottom)).save(
                    output_dir / f"{image_path.stem}_shot_{idx:02d}.png"
                )
                idx += 1


# ── rich (opzionale) ───────────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
    )
    from rich.table import Table

    _console = Console()
    RICH = True
except ImportError:
    _console = None  # type: ignore[assignment]
    RICH = False


# ── helpers ────────────────────────────────────────────────────────────────────


def _get_files(directory: Path) -> list[Path]:
    return sorted(
        p
        for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() in VALID_EXTENSIONS
    )


def _split_fn(mode: str):
    return _do_split_2x2 if mode == "2x2" else _do_split_3x3


def _frames_per_image(mode: str) -> int:
    return 4 if mode == "2x2" else 9


def _print_error(msg: str) -> None:
    if RICH:
        _console.print(f"[bold red]Errore:[/bold red] {msg}")
    else:
        print(f"Errore: {msg}", file=sys.stderr)


def _print_warn(msg: str) -> None:
    if RICH:
        _console.print(f"[yellow]Avviso:[/yellow] {msg}")
    else:
        print(f"Avviso: {msg}")


# ── core CLI run ───────────────────────────────────────────────────────────────


def run_cli(
    mode: str,
    input_dir: Path,
    output_dir: Path,
    single_file: Path | None = None,
) -> None:
    if single_file:
        if not single_file.is_file():
            _print_error(f"File non trovato: {single_file}")
            sys.exit(1)
        files = [single_file]
    else:
        if not input_dir.exists():
            _print_error(f"Cartella di input non trovata: {input_dir}")
            sys.exit(1)
        files = _get_files(input_dir)
        if not files:
            _print_warn(f"Nessuna immagine trovata in: {input_dir}")
            return

    output_dir.mkdir(parents=True, exist_ok=True)
    split = _split_fn(mode)
    frames_each = _frames_per_image(mode)

    if RICH:
        _console.print(
            Panel(
                f"[bold cyan]Modalità:[/bold cyan] {mode}   "
                f"[bold cyan]Input:[/bold cyan] {input_dir}   "
                f"[bold cyan]Output:[/bold cyan] {output_dir}",
                title="[bold green]Images Grid Split[/bold green]",
                expand=False,
            )
        )

        n_ok = n_err = n_frames = 0
        errors: list[tuple[str, str]] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn(
                "[progress.percentage]{task.percentage:>3.0f}%  "
                "[dim]{task.completed}/{task.total}[/dim]"
            ),
            TimeElapsedColumn(),
            console=_console,
        ) as prog:
            task = prog.add_task("Elaborazione…", total=len(files))
            for f in files:
                prog.update(task, description=f"[cyan]{f.name}[/cyan]")
                try:
                    split(f, output_dir)
                    n_ok += 1
                    n_frames += frames_each
                except Exception as exc:
                    n_err += 1
                    errors.append((f.name, str(exc)))
                prog.advance(task)

        table = Table(title="Riepilogo", show_header=True, header_style="bold magenta")
        table.add_column("Elaborate", style="green", justify="center")
        table.add_column("Frame generati", style="cyan", justify="center")
        table.add_column("Errori", style="red", justify="center")
        table.add_row(str(n_ok), str(n_frames), str(n_err))
        _console.print(table)

        for name, err in errors:
            _console.print(f"  [red]✗[/red] {name}: {err}")

        _console.print(
            f"\n[bold green]Output salvato in:[/bold green] {output_dir.resolve()}\n"
        )

    else:
        print(f"Images Grid Split — {mode}")
        print(f"Input: {input_dir}  →  Output: {output_dir}\n")
        n_ok = n_err = n_frames = 0
        for f in files:
            try:
                split(f, output_dir)
                n_ok += 1
                n_frames += frames_each
                print(f"  ✓  {f.name}  →  {frames_each} frame")
            except Exception as exc:
                n_err += 1
                print(f"  ✗  {f.name}: {exc}")
        print(f"\nElaborate: {n_ok}  |  Frame: {n_frames}  |  Errori: {n_err}")
        print(f"Output: {output_dir.resolve()}")


# ── argparse ───────────────────────────────────────────────────────────────────


def _add_split_subparser(subparsers, mode: str) -> None:
    default_in = f"input_grids_{mode}"
    default_out = f"output_frames_{mode}"
    frames = _frames_per_image(mode)

    p = subparsers.add_parser(
        mode,
        help=f"Divide griglie {mode} in {frames} immagini",
    )
    p.add_argument(
        "-i",
        "--input",
        default=default_in,
        metavar="DIR",
        help=f"Cartella di input  (default: {default_in})",
    )
    p.add_argument(
        "-o",
        "--output",
        default=default_out,
        metavar="DIR",
        help=f"Cartella di output (default: {default_out})",
    )
    p.add_argument(
        "-f",
        "--file",
        default=None,
        metavar="FILE",
        help="Elabora un singolo file invece dell'intera cartella",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="split_kling",
        description="Images Grid Split — divide griglie di immagini in frame separati.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
esempi:
  python split_kling.py 2x2
  python split_kling.py 3x3 -i mia_cartella -o output
  python split_kling.py 2x2 -f singola.png -o output
  python split_kling.py ui
""",
    )

    sub = parser.add_subparsers(dest="command", metavar="COMANDO")
    _add_split_subparser(sub, "2x2")
    _add_split_subparser(sub, "3x3")
    sub.add_parser("ui", help="Avvia l'interfaccia grafica")

    args = parser.parse_args()

    if args.command == "ui":
        import split_kling_ui

        split_kling_ui.launch()
        return

    if args.command is None:
        parser.print_help()
        return

    single = Path(args.file) if args.file else None
    run_cli(args.command, Path(args.input), Path(args.output), single)


if __name__ == "__main__":
    main()
