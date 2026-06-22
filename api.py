import grp
import os
import pwd
import re
import shutil
import subprocess
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="v-helper", docs_url=None, redoc_url=None)

# v-helper shares a version line with v-shipper — both bump together on each
# coordinated release. v-shipper reads this via /version to flag mismatches.
__version__ = "0.5.0"

_API_KEY = os.environ.get("API_KEY", "")
_VOLUME = Path(os.environ.get("VOLUME", "/data")).resolve()
# Host-namespace base path that VOLUME is mounted from. Docker reports mount sources in
# the host namespace, which differs from VOLUME inside this container. Falls back to
# VOLUME (identity) when unset.
_DOCKER_VOLUMES_HOST_PATH = os.environ.get("DOCKER_VOLUMES_HOST_PATH", str(_VOLUME)).rstrip("/")

# Octal mode (3-4 digits, each 0-7) and a single user/group token (numeric id or a
# name). Kept identical to v-shipper's validate_mode / validate_owner_token so input
# is rejected the same way at both ends. The owner spec is two tokens joined by ':'.
_MODE_RE = re.compile(r"^[0-7]{3,4}$")
_OWNER_TOKEN_RE = re.compile(r"^[0-9]+$|^[A-Za-z0-9_][A-Za-z0-9_.-]{0,31}$")


def _name_for_uid(uid: int) -> str:
    """Resolve a uid to a username, falling back to the numeric string."""
    try:
        return pwd.getpwuid(uid).pw_name
    except KeyError:
        return str(uid)


def _name_for_gid(gid: int) -> str:
    """Resolve a gid to a group name, falling back to the numeric string."""
    try:
        return grp.getgrgid(gid).gr_name
    except KeyError:
        return str(gid)


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


@app.get("/version")
def version(x_api_key: str = Header(default="")):
    _auth(x_api_key)
    return {"version": __version__}


@app.get("/fs/disk")
def disk(x_api_key: str = Header(default="")):
    _auth(x_api_key)
    usage = shutil.disk_usage(_VOLUME)
    return {
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
    }


@app.get("/fs/size")
def size(name: str, x_api_key: str = Header(default="")):
    _auth(x_api_key)
    target = _safe_child(name)
    if not target.exists():
        raise HTTPException(status_code=404, detail="Not found")
    # Recursive sum of regular-file bytes — identical semantics to v-shipper's
    # volume_service._get_dir_size: symlinks are NOT followed and NOT counted,
    # so a local↔remote migration verification compares like for like.
    total = 0
    try:
        if target.is_dir():
            for entry in target.rglob("*"):
                try:
                    if entry.is_file() and not entry.is_symlink():
                        total += entry.stat().st_size
                except OSError:
                    pass
        elif target.is_file() and not target.is_symlink():
            total = target.stat().st_size
    except OSError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"size_bytes": total}


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


@app.get("/fs/stat")
def stat_(name: str, x_api_key: str = Header(default="")):
    _auth(x_api_key)
    target = _safe_child(name)
    if not target.exists():
        raise HTTPException(status_code=404, detail="Not found")
    st = target.stat()
    return {
        "mode": oct(st.st_mode)[-3:],
        "uid": st.st_uid,
        "gid": st.st_gid,
        "user": _name_for_uid(st.st_uid),
        "group": _name_for_gid(st.st_gid),
    }


class ChmodRequest(BaseModel):
    name: str
    mode: str


@app.post("/fs/chmod")
def chmod(body: ChmodRequest, x_api_key: str = Header(default="")):
    _auth(x_api_key)
    target = _safe_child(body.name)
    if not target.exists():
        raise HTTPException(status_code=404, detail="Not found")
    if not _MODE_RE.match(body.mode):
        raise HTTPException(status_code=400, detail="Invalid mode")
    # subprocess with list args (no shell) — chmod -R, identical primitive to
    # v-shipper's local change_permissions so local and remote behave the same.
    result = subprocess.run(
        ["chmod", "-R", body.mode, str(target)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"chmod failed: {result.stderr.strip()}")
    return {"ok": True, "command": f"chmod -R {body.mode}", "output": result.stderr.strip()}


class ChownRequest(BaseModel):
    name: str
    owner: str


@app.post("/fs/chown")
def chown(body: ChownRequest, x_api_key: str = Header(default="")):
    _auth(x_api_key)
    target = _safe_child(body.name)
    if not target.exists():
        raise HTTPException(status_code=404, detail="Not found")
    # owner is a "user:group" spec; validate each token (numeric id or name).
    parts = body.owner.split(":")
    if len(parts) != 2 or not all(_OWNER_TOKEN_RE.match(p) for p in parts):
        raise HTTPException(status_code=400, detail="Invalid owner spec")
    result = subprocess.run(
        ["chown", "-R", body.owner, str(target)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"chown failed: {result.stderr.strip()}")
    return {"ok": True, "command": f"chown -R {body.owner}", "output": result.stderr.strip()}


@app.get("/docker/users")
def docker_users(x_api_key: str = Header(default="")):
    """Map each volume under VOLUME to the containers using it: {volume: [{name, status}]}.

    A container uses a volume if any of its mount sources equals the volume's host path
    (DOCKER_VOLUMES_HOST_PATH/<name>) or sits under it — covers sub-folder bind mounts
    and local-driver volumes whose mountpoint lives there. Returns {} (never errors) if
    the docker package or socket is unavailable.
    """
    _auth(x_api_key)
    result = {}
    try:
        names = [e.name for e in _VOLUME.iterdir() if e.is_dir() and not e.name.startswith(".")]
    except OSError:
        return result
    result = {name: [] for name in names}

    try:
        import docker
        client = docker.from_env()
        containers = []
        for c in client.containers.list(all=True):
            sources = [m.get("Source") for m in (c.attrs.get("Mounts") or []) if m.get("Source")]
            containers.append({"name": c.name, "status": c.status, "sources": sources})
        for name in names:
            host_path = f"{_DOCKER_VOLUMES_HOST_PATH}/{name}"
            prefix = host_path + "/"
            for c in containers:
                if any(s == host_path or s.startswith(prefix) for s in c["sources"]):
                    result[name].append({"name": c["name"], "status": c["status"]})
    except Exception as exc:
        print(f"[WARNING] docker_users failed: {exc}", flush=True)

    return result


@app.exception_handler(Exception)
async def _generic(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
