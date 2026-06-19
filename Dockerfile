FROM phusion/baseimage:noble-1.0.2

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install --no-install-suggests --no-install-recommends -y unzip curl wget iputils-ping \
    && apt-get upgrade -y -o Dpkg::Options::="--force-confold" \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && userdel --force --remove ubuntu

RUN apt-get update && \
  DEBIAN_FRONTEND=noninteractive apt-get install -yq --no-install-recommends rsync && \
  apt-get clean autoclean && \
  apt-get autoremove -y && \
  rm -rf /var/lib/{apt,dpkg,cache,log}/ && \
  mkdir /etc/service/rsyncd

ADD ./rsyncd.sh /etc/service/rsyncd/run
RUN chmod 0755 /etc/service/rsyncd/run

EXPOSE 873
VOLUME /data