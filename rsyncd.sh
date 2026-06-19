#!/bin/bash
set -e
source /etc/container_environment.sh

VOLUME=${VOLUME:-/data}
ALLOW=${ALLOW:-192.168.0.0/16 172.16.0.0/12}
OWNER=${OWNER:-nobody}
GROUP=${GROUP:-nogroup}
VOLUME_NAME=${VOLUME_NAME:-volume}
READ_ONLY=${READ_ONLY:-true}
COMMENT=${COMMENT:-"docker volume"}
MAX_CONNECTIONS=${MAX_CONNECTIONS:-20}
BWLIMIT=${BWLIMIT:-0}

chown "${OWNER}:${GROUP}" "${VOLUME}" || true

[ -f /etc/rsyncd.conf ] || cat <<EOF > /etc/rsyncd.conf
uid = ${OWNER}
gid = ${GROUP}
use chroot = yes
pid file = /var/run/rsyncd.pid
log file = /dev/stdout
max connections = ${MAX_CONNECTIONS}
strict modes = yes
ignore errors = no
ignore nonreadable = yes
transfer logging = no
timeout = 600
refuse options = checksum
dont compress = *.gz *.tgz *.zip *.z *.rpm *.deb *.iso *.bz2 *.tbz

[${VOLUME_NAME}]
    hosts deny = *
    hosts allow = ${ALLOW}
    read only = ${READ_ONLY}
    path = ${VOLUME}
    comment = "${COMMENT}"

EOF

OPTS="--no-detach --daemon --config /etc/rsyncd.conf"
if [ $BWLIMIT -gt 0 ]; then
  OPTS="$OPTS --bwlimit=${BWLIMIT}"
fi

exec /usr/bin/ionice -c3 /usr/bin/rsync ${OPTS}