# Copyright 2022 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from buildbot.plugins import changes, util

#FIXME:
# Get the repositorys info from the gentoo-ci db 
def gentoo_change_source(cs=[]):
    cs.append(changes.GitPoller(
            #repourl='https://github.com/zorry/gentoo.git',
            repourl='https://github.com/gentoo/gentoo.git',
            branches=True,
            workdir= 'repositorys' + '/gentoo.git/',
            pollAtLaunch=True,
            pollInterval=300,
            pollRandomDelayMin=20,
            pollRandomDelayMax=60,
            project='gentoo-ci'
            #sshPrivateKey = util.Secret("gitlab_ssh_pub_gentoo-ci"),
            #sshHostKey = util.Secret("gitlab_ssh_host_gentoo-ci")
    ))
    return cs
