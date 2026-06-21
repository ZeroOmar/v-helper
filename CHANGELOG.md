# Changelog

## 0.4.5

Version realigned with v-shipper — the two now share a single version line and bump together on each release (jumps from `0.3.1` to match v-shipper `0.4.5`).

### Added

- **`GET /version` endpoint** — reports the v-helper version as `{"version": "x.y.z"}`. v-shipper reads it to detect version drift between the pair and surface "out of date" warnings.
- **`GET /fs/size` endpoint** — returns the recursive byte total of a volume (`?name=<vol>` → `{"size_bytes": N}`), counting regular files only and excluding symlinks. This matches v-shipper's local `_get_dir_size` exactly, so local↔remote migration verification compares like for like instead of disagreeing over symlink byte counts. Used by v-shipper in place of the rsync `--list-only` size estimate when v-helper is configured.

## 0.3.1

### Fixed

- **`POST /fs/rm` now tolerates mixed ownership and permissions** — the endpoint used `shutil.rmtree`/`unlink`, which raised `Permission denied` on volume trees containing files owned by other container users; it now uses `rm -rf` (running as root) so deletes succeed regardless of file ownership. This keeps the delete primitive identical to v-shipper's `volume_service.rm_rf`.

## 0.3.0

### Added

- **`POST /fs/rm` endpoint** — deletes a volume directory (recursive) or file inside `VOLUME`. Used by v-shipper when deleting a remote volume; running the delete through the API avoids the permission errors that arise when the rsync daemon user lacks write access to files owned by container users. Body: `{"name": "vol_name"}`. Returns `404` if the target doesn't exist, `500` on OS error.

## 0.2.1

### Fixed

- **Quick-start example used wrong volume mount path** — the `docker run` example mounted the host path to itself (`/mnt/docker-volumes:/mnt/docker-volumes`) and set `VOLUME` to that same path, but the container's data path should be `/data`; corrected to `-v /mnt/docker-volumes:/data -e VOLUME=/data`

### Changed

- **Release skill updated** — `.claude/commands/release.md` was a copy of the v-shipper skill; rewritten for v-helper (correct diff scope, no `app/models.py` version field, updated semver rules)

## 0.2.0

### Added
- **HTTP control API** — FastAPI service on port `8888` (configurable via `API_PORT`) that v-shipper uses for operations rsync cannot perform: `GET /fs/disk` (real free/total bytes), `GET /fs/ls` (directory listing with modification timestamps), `POST /fs/mkdir` (create volume directory), `POST /fs/rename` (rename volume). All endpoints require `X-API-Key` auth; paths are validated to stay within `VOLUME`.
- **`API_KEY` env var** — shared secret for the control API; if unset, all API requests return `503`.
- **`API_PORT` env var** — API listen port (default `8888`).

## 0.1.1

### Fixed
- **Service `run` script now executable** — `rsyncd.sh` was copied to `/etc/service/rsyncd/run` without an execute bit, so runit failed with `runsv rsyncd: fatal: unable to start ./run: access denied` and the container never started rsync. The Dockerfile now `chmod 0755`s the script and the tracked source is marked executable.

## 0.1.0

### Added
- **Initial release** — Docker rsync-daemon volume container, used as a remote-pool target for v-shipper.
- **Configurable rsync share** — environment variables for `VOLUME`, `ALLOW`, `VOLUME_NAME`, `COMMENT`, `READ_ONLY`, `OWNER`/`GROUP`, `BWLIMIT`, and `MAX_CONNECTIONS`.
- **Multi-platform publishing** — GitHub Actions workflow builds and cosign-signs the image to GHCR on `*.*.*` tags.
