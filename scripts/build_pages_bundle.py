from __future__ import annotations

import argparse
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

SOURCE_DIRECTORIES = [
    Path("docs/pages"),
    Path("views/application/demo_bus_routes_nyc"),
    Path("views/application/demo_bus_routes_nyc_single_scenario"),
    Path("views/static/demo_bus_routes_nyc"),
]

ROOT_INDEX = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0; url=./docs/pages/index.html">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Route Contribution Intelligence</title>
</head>
<body>
  <p>Redirecting to <a href="./docs/pages/index.html">the documentation site</a>...</p>
  <script>
    window.location.replace("./docs/pages/index.html");
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a GitHub Pages bundle with docs and demo outputs."
    )
    parser.add_argument(
        "--output",
        default=".pages-site",
        help="Relative or absolute path for the generated Pages bundle.",
    )
    return parser.parse_args()


def copy_tree(source_relative: Path, destination_root: Path) -> None:
    source_path = REPO_ROOT / source_relative
    if not source_path.exists():
        raise FileNotFoundError(f"Missing source directory: {source_path}")

    destination_path = destination_root / source_relative
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_path, destination_path)


def build_bundle(output_path: Path) -> None:
    if output_path.exists():
        shutil.rmtree(output_path)

    output_path.mkdir(parents=True, exist_ok=True)

    for source_relative in SOURCE_DIRECTORIES:
        copy_tree(source_relative, output_path)

    (output_path / ".nojekyll").write_text("", encoding="utf-8")
    (output_path / "index.html").write_text(ROOT_INDEX, encoding="utf-8")


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path

    build_bundle(output_path)
    print(f"Built Pages bundle at {output_path}")


if __name__ == "__main__":
    main()
