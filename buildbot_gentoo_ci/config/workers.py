# Copyright 2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from buildbot.plugins import worker

def gentoo_workers(w=[]):
    w.append(worker.LocalWorker('updatedb_1'))
    return w
