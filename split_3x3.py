import argparse
from pathlib import Path

from PIL import Image

DEFAULT_INPUT_DIR = "input_grids_3x3"
DEFAULT_OUTPUT_DIR = "output_frames_3x3"
VALID_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def split_image_3x3(image_path: Path, output_dir: Path) -> None:
    with Image.open(image_path) as img:
        width, height = img.size

        if width < 3 or height < 3:
            print(f"Saltata {image_path.name}: immagine troppo piccola.")
            return

        cell_width = width // 3
        cell_height = height // 3

        index = 1
        for row in range(3):
            for col in range(3):
                left = col * cell_width
                top = row * cell_height

                right = width if col == 2 else (col + 1) * cell_width
                bottom = height if row == 2 else (row + 1) * cell_height

                box = (left, top, right, bottom)
                cropped = img.crop(box)

                output_path = output_dir / f"{image_path.stem}_shot_{index:02d}.png"
                cropped.save(output_path)
                index += 1

        print(f"Completata: {image_path.name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Divide immagini grid 3x3 in 9 immagini separate."
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
        split_image_3x3(image_path, output_dir)


if __name__ == "__main__":
    main()
