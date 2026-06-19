# Changelog

## 0.1.0

### Added
- **Initial release** — Docker rsync-daemon volume container, used as a remote-pool target for v-shipper.
- **Configurable rsync share** — environment variables for `VOLUME`, `ALLOW`, `VOLUME_NAME`, `COMMENT`, `READ_ONLY`, `OWNER`/`GROUP`, `BWLIMIT`, and `MAX_CONNECTIONS`.
- **Multi-platform publishing** — GitHub Actions workflow builds and cosign-signs the image to GHCR on `*.*.*` tags.
