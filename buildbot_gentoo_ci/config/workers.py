# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from buildbot.plugins import worker

def gentoo_workers(w=[]):
    # FIXME: Get workers from db
    w.append(worker.LocalWorker('updatedb_1'))
    w.append(worker.LocalWorker('updatedb_2'))
    w.append(worker.LocalWorker('updatedb_3'))
    w.append(worker.LocalWorker('updatedb_4'))
    w.append(worker.Worker('bot-test', 'test1234'))
    return w
