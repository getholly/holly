import re
from pathlib import Path

THEME_FILE = Path(__file__).resolve().parents[2] / "frontend/src/lib/store/theme.ts"
STATIC_DIR = Path(__file__).resolve().parents[2] / "frontend/static"

IMG_PATTERN = re.compile(r"\"(img/[^\"]+\.(?:png|jpg|jpeg|webp|svg))\"")


def test_theme_images_exist():
    content = THEME_FILE.read_text()
    matches = IMG_PATTERN.findall(content)
    assert matches, "no image paths found in theme.ts"

    missing = [m for m in matches if not (STATIC_DIR / m).is_file()]
    assert not missing, f"missing image files: {missing}"

    assert all(not m.startswith("/") for m in matches)

