# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from twisted.internet import defer

from buildbot.plugins import util
from buildbot_gentoo_ci.config import buildfactorys
from buildbot_gentoo_ci.config.workers import gentoo_ci_workers

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

# Use same worker as update_cpv_data was done by so we have same git commit
def CanWorkerUpdateV(builder, wfb, request):
    print(request.properties['cp_worker'])
    print(wfb)
    if wfb.worker.workername == request.properties['cp_worker']:
        return True
    return False

def gentoo_builders(worker_data):
    b = []
    g_ci_w = gentoo_ci_workers(worker_data)
    b.append(util.BuilderConfig(
        name='update_db_check',
        workername=g_ci_w.getWorkersUuid('local')[0],
        workerbuilddir='builds',
        collapseRequests=False,
        factory=buildfactorys.update_db_check()
        )
    )
    b.append(util.BuilderConfig(
        name='update_repo_check',
        workername=g_ci_w.getWorkersUuid('local')[1],
        workerbuilddir='builds',
        collapseRequests=True,
        factory=buildfactorys.update_repo_check()
        )
    )
    # update cpv in db and call build_request_data
    #FIXME: look so we don't run parallel with diffrent worker
    # (builders.UpdateRepos step)
    b.append(util.BuilderConfig(
        name='update_cpv_data',
        workernames=g_ci_w.getWorkersUuid('log')[0],
        workerbuilddir='builds',
        collapseRequests=False,
        factory=buildfactorys.update_db_cpv()
        )
    )
    # Use multiplay workers
    b.append(util.BuilderConfig(
        name='update_v_data',
        workername=g_ci_w.getWorkersUuid('log')[0],
        workerbuilddir='builds',
        collapseRequests=False,
        canStartBuild=CanWorkerUpdateV,
        factory=buildfactorys.update_db_v()
        )
    )
    # Use multiplay workers
    b.append(util.BuilderConfig(
        name='build_request_data',
        workernames=g_ci_w.getWorkersUuid('local'),
        collapseRequests=False,
        factory=buildfactorys.build_request_check()
        )
    )
    # Use multiplay workers
    b.append(util.BuilderConfig(
        name='run_build_request',
        workernames=g_ci_w.getWorkersUuid('docker'),
        canStartBuild=CanWorkerBuildProject,
        collapseRequests=False,
        factory=buildfactorys.run_build_request()
        )
    )
    # Use multiplay workers
    b.append(util.BuilderConfig(
        name='parse_build_log',
        workernames=g_ci_w.getWorkersUuid('log')[1:],
        collapseRequests=False,
        factory=buildfactorys.parse_build_log()
        )
    )
    # For node workers
    b.append(util.BuilderConfig(
        name='run_build_stage4_request',
        workernames=g_ci_w.getWorkersUuid('node'),
        #FIXME: support more the one node
        #canStartBuild=CanWorkerBuildProject,
        collapseRequests=False,
        factory=buildfactorys.run_build_stage4_request()
        )
    )
    return b
