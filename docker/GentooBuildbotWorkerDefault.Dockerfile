# name the portage image
FROM gentoo/portage:latest as portage

# based on stage3 image
FROM gentoo/stage3:latest

# copy the entire portage volume in
COPY --from=portage /var/db/repos/gentoo /var/db/repos/gentoo

# Setup portage
# emerge needed deps buildbot-worker, psycopg, git and sqlalchemy
# get the needed buildbot-worker config
RUN echo -e "[binhost]\npriority = 9999\nsync-uri = https://gentoo.osuosl.org/experimental/amd64/binpkg/default/linux/17.1/x86-64/\n" | cat >> /etc/portage/binrepos.conf\
 && echo 'EMERGE_DEFAULT_OPTS="--binpkg-respect-use=n --usepkg=y --getbinpkg=y --autounmask-write --autounmask-continue --autounmask-keep-keywords=y --autounmask-use=y"' | cat >> /etc/portage/m>
 && echo 'FEATURES="-ipc-sandbox -pid-sandbox -network-sandbox -usersandbox -mount-sandbox sandbox"' | cat >> /etc/portage/make.conf\
 && echo 'FEATURES="${FEATURES} parallel-install parallel-fetch -merge-sync"' | cat >> /etc/portage/make.conf\
 && echo 'FEATURES="${FEATURES} buildpkg"' | cat >> /etc/portage/make.conf\
 && echo 'MAKEOPTS="-j8"' | cat >> /etc/portage/make.conf\
 && echo 'dev-vcs/git -webdev -gnome-keyring' | cat >> /etc/portage/package.use/git\
 && echo 'dev-util/buildbot-worker' | cat >> /etc/portage/package.accept_keywords/buildbot\
 && echo 'dev-libs/glib' | cat >> /etc/portage/package.mask/git\
 && emerge -qv buildbot-worker sqlalchemy dev-python/psycopg rust-bin dev-vcs/git
 #&& chown buildbot:buildbot /var/lib/buildbot_worker

#FIXME: run worker as buildbot (git fail)
#USER buildbot
WORKDIR /var/lib/buildbot_worker
RUN wget https://raw.githubusercontent.com/buildbot/buildbot/master/worker/docker/buildbot.tac
ENTRYPOINT ["/usr/bin/buildbot-worker"]
CMD ["start", "--nodaemon"]
