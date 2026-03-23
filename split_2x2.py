import argparse
from pathlib import Path

from PIL import Image

DEFAULT_INPUT_DIR = "input_grids_2x2"
DEFAULT_OUTPUT_DIR = "output_frames_2x2"
VALID_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def split_image_2x2(image_path: Path, output_dir: Path) -> None:
    with Image.open(image_path) as img:
        width, height = img.size

        if width < 2 or height < 2:
            print(f"Saltata {image_path.name}: immagine troppo piccola.")
            return

        half_width = width // 2
        half_height = height // 2

        quadrants = [
            ("01_top_left", (0, 0, half_width, half_height)),
            ("02_top_right", (half_width, 0, width, half_height)),
            ("03_bottom_left", (0, half_height, half_width, height)),
            ("04_bottom_right", (half_width, half_height, width, height)),
        ]

        for label, box in quadrants:
            cropped = img.crop(box)
            output_path = output_dir / f"{image_path.stem}_{label}.png"
            cropped.save(output_path)

        print(f"Completata: {image_path.name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Divide immagini grid 2x2 in 4 immagini separate."
    )
    parser.add_argument(
        "-i",
        "--input",
        default=DEFAULT_INPUT_DIR,
        help=f"Cartella di input (default: {DEFAULT_INPUT_DIR})",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Cartella di output (default: {DEFAULT_OUTPUT_DIR})",
    )
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        print(f"La cartella di input non esiste: {input_dir}")
        return

    image_files = [
        path
        for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in VALID_EXTENSIONS
    ]

    if not image_files:
        print(f"Nessuna immagine trovata in {input_dir}")
        return

    for image_path in sorted(image_files):
        split_image_2x2(image_path, output_dir)


if __name__ == "__main__":
    main()
