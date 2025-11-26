from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence, Tuple

from fastapi import UploadFile
from loguru import logger


class FileService:
    """Service for saving uploaded files inside a base directory."""

    def __init__(self, base_dir: str | Path = "/data") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized FileService with base directory: {self.base_dir}")

    def _sanitize_dir(self, target_dir: str | None) -> Path:
        if not target_dir:
            return self.base_dir
        cleaned = target_dir.lstrip("/")
        parts = [p for p in Path(cleaned).parts if p not in {"..", ".", ""}]
        safe = Path(*parts)
        final = (self.base_dir / safe).resolve()
        base_resolved = self.base_dir.resolve()
        if base_resolved != final and base_resolved not in final.parents:
            raise ValueError("Invalid target directory")
        final.mkdir(parents=True, exist_ok=True)
        return final

    async def save_files(self, files: Sequence[UploadFile], target_dir: str | None = None) -> Tuple[Path, list[str]]:
        directory = self._sanitize_dir(target_dir)
        saved: list[str] = []
        for upload in files:
            contents = await upload.read()
            dest = directory / upload.filename
            with open(dest, "wb") as out_file:
                out_file.write(contents)
            saved.append(str(dest))
        return directory, saved
