# Changelog

## 0.1.1

### Fixed
- **Service `run` script now executable** — `rsyncd.sh` was copied to `/etc/service/rsyncd/run` without an execute bit, so runit failed with `runsv rsyncd: fatal: unable to start ./run: access denied` and the container never started rsync. The Dockerfile now `chmod 0755`s the script and the tracked source is marked executable.

## 0.1.0

### Added
- **Initial release** — Docker rsync-daemon volume container, used as a remote-pool target for v-shipper.
- **Configurable rsync share** — environment variables for `VOLUME`, `ALLOW`, `VOLUME_NAME`, `COMMENT`, `READ_ONLY`, `OWNER`/`GROUP`, `BWLIMIT`, and `MAX_CONNECTIONS`.
- **Multi-platform publishing** — GitHub Actions workflow builds and cosign-signs the image to GHCR on `*.*.*` tags.
