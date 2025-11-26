from __future__ import annotations

import os
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from rest_mcp_client.services.file_service import FileService

router = APIRouter(prefix="/api/files", tags=["files"])

file_service = FileService(base_dir=os.environ.get("BASE_DIR", "/data"))


class UploadFilesResponse(BaseModel):
    success: bool
    message: str
    files: List[str]
    directory: str


@router.post("/upload", response_model=UploadFilesResponse)
async def upload_files(
    files: List[UploadFile] = File(...),
    target_dir: str | None = Form(None),
) -> UploadFilesResponse:
    try:
        directory, saved = await file_service.save_files(files, target_dir)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))

    relative_dir = str(Path(directory).relative_to(file_service.base_dir)) if directory != file_service.base_dir else ""
    return UploadFilesResponse(
        success=True,
        message="Files uploaded successfully",
        files=[str(Path(p).name) for p in saved],
        directory=relative_dir,
    )
