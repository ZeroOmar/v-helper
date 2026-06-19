# Changelog

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
