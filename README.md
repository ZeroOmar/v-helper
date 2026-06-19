# V-Helper

A helper Container to work with V-Shipper and act as a remote Pool

## Usage

First, you can launch a volume container exposing a volume with rsync.

```sh
$ CID=$(docker run -d -p 10873:873 -v /tmp/:/data --name rsyncd ghcr.io/zeroomar/v-helper:latest)
```

You can connect to rsync server inside a container like this:

```sh
$ rsync rsync://<docker>:10873/
volume          docker volume
```

To sync:

```sh
$ rsync -avP /path/to/dir rsync://<docker>:10873/volume/
```

Next, you can launch a container connected with the volume under `/data`.

```sh
$ docker run -it --volumes-from $CID ubuntu /bin/sh
```

## Advanced

In default, rsync server accepts a connection only from `192.168.0.0/16` and `172.12.0.0/12` for security reasons.
You can override via an environment variable like this:

```sh
$ docker run -d -p 10873:873 -e ALLOW='10.0.0.0/8 x.x.x.x/y' ghcr.io/zeroomar/v-helper:latest
```

## All Variables

* `VOLUME` - Define the volume path (default: `/data`)
* `ALLOW` - Which network segments to allow (default: `192.168.0.0/16 172.16.0.0/12`)
* `VOLUME_NAME` - The logical name of the volume (default: `volume`)
* `COMMENT` - The share comment (default: `docker volume`)
* `READ_ONLY` - A boolean to set if the share should be read-only or not (default: `true`)
* `OWNER/GROUP` - Define the owner/group name or uid/gid to use (default: `nobody/nogroup`)
* `BWLIMIT` - Bandwidth limit in Kb/s (default: `0`)
* `MAX_CONNECTIONS` - Maximum number of connections (default: `20`)



### Based on https://github.com/metabrainz/docker-rsyncd