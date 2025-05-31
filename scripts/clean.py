import shutil
import sys
from pathlib import Path

PYCACHE = "__pycache__"
DIRS = (
    PYCACHE,
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".qodo",
    "dist",
    "output_dir",
)


def remove_dir(path: Path, *, dry_run: bool = False) -> None:
    if path.is_dir():
        if dry_run:
            print(f"[dry run] Would delete {path}")
        else:
            print(f"Deleting {path}")
            shutil.rmtree(path, ignore_errors=True)


def find_and_remove_pycache(root: Path = Path(), *, dry_run: bool = False) -> None:
    for pycache_dir in root.rglob(PYCACHE):
        remove_dir(pycache_dir, dry_run=dry_run)


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    for dir_ in DIRS:
        remove_dir(Path(dir_), dry_run=dry_run)
    find_and_remove_pycache(dry_run=dry_run)
