# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from buildbot.plugins import util
from buildbot_gentoo_ci.config import buildfactorys

# FIXME: get workers from db or file
LocalWorkers = []
LocalWorkers.append('updatedb_1')
LocalWorkers.append('updatedb_2')
LocalWorkers.append('updatedb_3')
LocalWorkers.append('updatedb_4')

def gentoo_builders(b=[]):
    b.append(util.BuilderConfig(
        name='update_db_check',
        workername='updatedb_1',
        workerbuilddir='builds',
        collapseRequests=False,
        factory=buildfactorys.update_db_check()
        )
    )
    b.append(util.BuilderConfig(
        name='update_repo_check',
        workername='updatedb_2',
        workerbuilddir='builds',
        collapseRequests=True,
        factory=buildfactorys.update_repo_check()
        )
    )
    # Use multiplay workers depend on Property(cp)
    # if cp do not match next one, use diffrent worker then
    # or first cp have done its buildsteps.
    # first LocalWorker need to be done before we can use mulitplay workers (git pull)
    b.append(util.BuilderConfig(
        name='update_cpv_data',
        workernames=LocalWorkers,
        workerbuilddir='builds',
        collapseRequests=False,
        factory=buildfactorys.update_db_cp()
        )
    )
    # Use multiplay workers
    b.append(util.BuilderConfig(
        name='update_v_data',
        workernames=LocalWorkers,
        workerbuilddir='builds',
        collapseRequests=False,
        factory=buildfactorys.update_db_v()
        )
    )
    # Use multiplay workers
    b.append(util.BuilderConfig(
        name='build_request_data',
        workernames=LocalWorkers,
        collapseRequests=False,
        factory=buildfactorys.build_request_check()
        )
    )
    # FIXME: get workers from db or file
    # Use multiplay workers
    b.append(util.BuilderConfig(
        name='run_build_request',
        workername='bot-test',
        collapseRequests=False,
        factory=buildfactorys.run_build_request()
        )
    )
    # Use multiplay workers
    b.append(util.BuilderConfig(
        name='parse_build_log',
        workernames=LocalWorkers,
        collapseRequests=False,
        factory=buildfactorys.parse_build_log()
        )
    )
    return b
