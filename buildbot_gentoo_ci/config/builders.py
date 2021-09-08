# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from twisted.internet import defer

from buildbot.plugins import util
from buildbot_gentoo_ci.config import buildfactorys

# FIXME: get LocalWorkers and BuildWorkers from db or file
LocalWorkers = []
LocalWorkers.append('updatedb_1')
LocalWorkers.append('updatedb_2')
LocalWorkers.append('updatedb_3')
LocalWorkers.append('updatedb_4')

BuildWorkers = []
BuildWorkers.append('a89c2c1a-46e0-4ded-81dd-c51afeb7fcfd')

@defer.inlineCallbacks
def CanWorkerBuildProject(builder, wfb, request):
    gentooci = builder.master.namedServices['services'].namedServices['gentooci']
    project_build_data = request.properties['project_build_data']
    project_workers = yield gentooci.db.projects.getWorkersByProjectUuid(project_build_data['project_uuid'])
    print(project_workers)
    print(wfb)
    for worker in project_workers:
        if wfb.worker.workername == worker['worker_uuid']:
            return True
    print('no worker')
    return False

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
    # Use multiplay workers
    b.append(util.BuilderConfig(
        name='run_build_request',
        workernames=BuildWorkers,
        canStartBuild=CanWorkerBuildProject,
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
