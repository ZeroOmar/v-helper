# v-helper

A helper container for [v-shipper](https://github.com/ZeroOmar/v-shipper) that acts as a remote pool. It exposes two services:

- **rsync daemon** (port `873`) — used by v-shipper for all file transfer operations
- **HTTP control API** (port `8888`) — used by v-shipper for filesystem operations that rsync cannot perform (create directory, rename, disk free space, modification timestamps)

## Quick start

```sh
docker run -d \
  -p 10873:873 \
  -p 8888:8888 \
  -v /mnt/docker-volumes:/data \
  -e VOLUME=/data \
  -e ALLOW='10.0.0.0/8' \
  -e READ_ONLY=false \
  -e VOLUME_NAME=docker-volumes \
  -e API_KEY=your-secret-key \
  ghcr.io/zeroomar/v-helper:latest
```

## rsync Variables

| Variable | Default | Description |
|---|---|---|
| `VOLUME` | `/data` | Volume path served by both rsync and the API |
| `ALLOW` | `192.168.0.0/16 172.16.0.0/12` | Allowed client networks (space-separated CIDR) |
| `VOLUME_NAME` | `volume` | rsync module name |
| `COMMENT` | `docker volume` | rsync module comment |
| `READ_ONLY` | `true` | Set `false` to allow rsync writes |
| `OWNER` / `GROUP` | `nobody` / `nogroup` | File ownership for rsync transfers |
| `BWLIMIT` | `0` | Bandwidth limit in KB/s (`0` = unlimited) |
| `MAX_CONNECTIONS` | `20` | Max concurrent rsync connections |

## API Variables

| Variable | Default | Description |
|---|---|---|
| `API_KEY` | *(required)* | Shared secret; all API requests must include `X-API-Key: <value>` |
| `API_PORT` | `8888` | Port for the HTTP control API |

If `API_KEY` is not set, all API requests return `503`.

## API Endpoints

All endpoints require the header `X-API-Key: <API_KEY>`.

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `GET` | `/fs/disk` | Disk usage for `VOLUME` (`total_bytes`, `used_bytes`, `free_bytes`) |
| `GET` | `/fs/ls` | Directory listing (`name`, `size_bytes`, `mtime_epoch`, `is_dir`) |
| `POST` | `/fs/mkdir` | Create a directory: `{"name": "vol_name"}` |
| `POST` | `/fs/rename` | Rename: `{"src": "old_name", "dst": "new_name"}` |
| `POST` | `/fs/rm` | Delete a volume or file: `{"name": "vol_name"}` |

All path inputs are validated to stay within `VOLUME`.

## Based on

[metabrainz/docker-rsyncd](https://github.com/metabrainz/docker-rsyncd)
