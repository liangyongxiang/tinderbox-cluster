# name the portage image
FROM gentoo/portage:latest as portage

# based on stage3 image
FROM gentoo/stage3:latest

# copy the entire portage volume in
COPY --from=portage /var/db/repos/gentoo /var/db/repos/gentoo

# Setup portage
# emerge needed deps buildbot-worker, psycopg and sqlalchemy
# get the needed buildbot-worker config
RUN echo -e "[binhost]\npriority = 9999\nsync-uri = https://gentoo.osuosl.org/experimental/amd64/binpkg/default/linux/17.1/x86-64/\n" | cat >> /etc/portage/binrepos.conf\
 && echo 'EMERGE_DEFAULT_OPTS="--binpkg-respect-use=n --usepkg=y --getbinpkg=y --autounmask-write --autounmask-continue --autounmask-keep-keywords=y --autounmask-use=y"' | cat >> /etc/portage/make.conf\
 && echo 'FEATURES="-ipc-sandbox -pid-sandbox -network-sandbox -usersandbox -mount-sandbox -sandbox"' | cat >> /etc/portage/make.conf\
 && echo 'FEATURES="${FEATURES} parallel-install parallel-fetch -merge-sync"' | cat >> /etc/portage/make.conf\
 && echo 'FEATURES="${FEATURES} buildpkg"' | cat >> /etc/portage/make.conf\
 && echo 'MAKEOPTS="-j8"' | cat >> /etc/portage/make.conf\
 && echo 'dev-util/buildbot-worker' | cat >> /etc/portage/package.accept_keywords/buildbot\
 && emerge -qv buildbot-worker sqlalchemy dev-python/psycopg rust-bin\
 && wget https://raw.githubusercontent.com/buildbot/buildbot/master/worker/docker/buildbot.tac\
 && cp buildbot.tac /var/lib/buildbot_worker/buildbot.tac

WORKDIR /var/lib/buildbot_worker
ENTRYPOINT ["/usr/bin/buildbot-worker"]
CMD ["start", "--nodaemon"]
