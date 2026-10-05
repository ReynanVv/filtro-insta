from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .moderation import moderate_image, moderate_video

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(100 * 1024 * 1024)))

app = FastAPI(
    title="Filtro Insta - API de moderação",
    version="0.1.0",
    description="Moderação pré-publicação de imagens e vídeos usando NudeNet.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/moderate")
async def moderate(file: UploadFile = File(...)) -> dict:
    content_type = (file.content_type or "").lower()
    if not (content_type.startswith("image/") or content_type.startswith("video/")):
        raise HTTPException(
            status_code=415,
            detail="Envie uma imagem ou vídeo.",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")

    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo maior que o limite de {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    try:
        if content_type.startswith("image/"):
            result = moderate_image(data)
            media_type = "image"
        else:
            suffix = Path(file.filename or "video.mp4").suffix or ".mp4"
            result = moderate_video(data, suffix=suffix)
            media_type = "video"
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Falha ao analisar o conteúdo.",
        ) from exc

    return {
        "filename": file.filename,
        "media_type": media_type,
        **result,
    }
