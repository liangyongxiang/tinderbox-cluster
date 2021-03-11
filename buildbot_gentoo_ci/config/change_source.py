# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from buildbot.plugins import changes, util

#FIXME:
# Get the repositorys info from the gentoo-ci db 
def gentoo_change_source(cs=[]):
    cs.append(changes.GitPoller(
            repourl='https://github.com/gentoo/gentoo.git',
            branches=True,
            workdir= 'repositorys' + '/gentoo.git/',
            pollInterval=240,
            pollRandomDelayMin=20,
            pollRandomDelayMax=60,
            project='gentoo'
    ))
    return cs
