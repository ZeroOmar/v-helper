import os
import shutil
import subprocess
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="v-helper", docs_url=None, redoc_url=None)

_API_KEY = os.environ.get("API_KEY", "")
_VOLUME = Path(os.environ.get("VOLUME", "/data")).resolve()


def _auth(x_api_key: str = ""):
    if not _API_KEY:
        raise HTTPException(status_code=503, detail="API_KEY not configured")
    if x_api_key != _API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")


def _safe_child(name: str) -> Path:
    """Resolve name as a single child of VOLUME; reject traversal attempts."""
    if not name or "/" in name or name in (".", ".."):
        raise HTTPException(status_code=400, detail="Invalid name")
    resolved = (_VOLUME / name).resolve()
    if not str(resolved).startswith(str(_VOLUME) + os.sep) and resolved != _VOLUME:
        raise HTTPException(status_code=400, detail="Path outside volume")
    return resolved


@app.get("/health")
def health(x_api_key: str = Header(default="")):
    _auth(x_api_key)
    return {"ok": True}


@app.get("/fs/disk")
def disk(x_api_key: str = Header(default="")):
    _auth(x_api_key)
    usage = shutil.disk_usage(_VOLUME)
    return {
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
    }


@app.get("/fs/ls")
def ls(x_api_key: str = Header(default="")):
    _auth(x_api_key)
    entries = []
    try:
        for entry in sorted(_VOLUME.iterdir(), key=lambda e: e.name):
            try:
                stat = entry.stat()
                entries.append({
                    "name": entry.name,
                    "size_bytes": stat.st_size,
                    "mtime_epoch": stat.st_mtime,
                    "is_dir": entry.is_dir(),
                })
            except OSError:
                pass
    except PermissionError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return entries


class MkdirRequest(BaseModel):
    name: str


@app.post("/fs/mkdir")
def mkdir(body: MkdirRequest, x_api_key: str = Header(default="")):
    _auth(x_api_key)
    target = _safe_child(body.name)
    if target.exists():
        raise HTTPException(status_code=409, detail="Already exists")
    try:
        target.mkdir(mode=0o777, parents=False)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"ok": True}


class RenameRequest(BaseModel):
    src: str
    dst: str


@app.post("/fs/rename")
def rename(body: RenameRequest, x_api_key: str = Header(default="")):
    _auth(x_api_key)
    src = _safe_child(body.src)
    dst = _safe_child(body.dst)
    if not src.exists():
        raise HTTPException(status_code=404, detail="Source not found")
    if dst.exists():
        raise HTTPException(status_code=409, detail="Destination already exists")
    try:
        src.rename(dst)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"ok": True}


class RmRequest(BaseModel):
    name: str


@app.post("/fs/rm")
def rm(body: RmRequest, x_api_key: str = Header(default="")):
    _auth(x_api_key)
    target = _safe_child(body.name)
    if not target.exists():
        raise HTTPException(status_code=404, detail="Not found")
    try:
        # Identical delete primitive to v-shipper's volume_service.rm_rf:
        # `rm -rf` runs as the container user (root) so it tolerates nested
        # trees and mixed ownership/permissions that rmtree/unlink choke on.
        subprocess.run(["rm", "-rf", "--", str(target)], check=True)
    except subprocess.CalledProcessError as exc:
        raise HTTPException(status_code=500, detail=f"rm failed: {exc}")
    return {"ok": True}


@app.exception_handler(Exception)
async def _generic(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
