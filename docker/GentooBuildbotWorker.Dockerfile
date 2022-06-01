# This Dockerfile creates a gentoo buildbot worker container image
# from a gentoo project stage4 docker image.

ARG PROJECTUUID

FROM stage4-${PROJECTUUID}
RUN echo "Building Gentoo Buildbot worker Container image for ${PROJECTUUID}" \
 && ( sed -i -e 's/#rc_sys=""/rc_sys="docker"/g' etc/rc.conf 2>/dev/null || true ) \
 && echo 'UTC' > etc/timezone \
 && echo 'docker' >> /var/lib/buildbot_worker/info/host \
 && echo 'bb-worker-${PROJECTUUID}:latest' >> /var/lib/buildbot_worker/info/host
WORKDIR /var/lib/buildbot_worker
ENTRYPOINT ["/usr/bin/buildbot-worker"]
CMD ["start", "--nodaemon"]
