# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from buildbot.plugins import worker

class gentoo_ci_workers():
    def __init__(self, worker_data, **kwargs):
        self.worker_data = worker_data

    def getLocalWorkersUuid(self):
        local_worker = []
        for worker in self.worker_data:
            if worker['type'] == 'local' and worker['enable'] is True:
                local_worker.append(worker['uuid'])
        print(local_worker)
        return local_worker

    def getBuildWorkersUuid(self):
        build_worker = []
        for worker in self.worker_data:
            if (worker['type'] != 'local' and worker['type'] != 'node') and worker['enable'] is True:
                build_worker.append(worker['uuid'])
        print(build_worker)
        return build_worker

    def getBuildWorkersAllData(self):
        build_worker = []
        for worker in self.worker_data:
            if (worker['type'] != 'local' and worker['type'] != 'node') and worker['enable'] is True:
                build_worker.append(worker)
        print(build_worker)
        return build_worker

    def getNodeWorkersUuid(self):
        node_worker = []
        for worker in self.worker_data:
            if worker['type'] == 'node' and worker['enable'] is True:
                node_worker.append(worker['uuid'])
        print(node_worker)
        return node_worker

    def getNodedWorkersAllData(self):
        node_worker = []
        for worker in self.worker_data:
            if worker['type'] == 'node' and worker['enable'] is True:
                node_worker.append(worker)
        print(node_worker)
        return node_worker

def gentoo_workers(worker_data):
    w = []
    g_ci_w = gentoo_ci_workers(worker_data)
    LocalWorkers = g_ci_w.getLocalWorkersUuid()
    BuildWorkers = g_ci_w.getBuildWorkersAllData()
    NodeWorkers = g_ci_w.getNodedWorkersAllData()
    for local_worker in LocalWorkers:
        w.append(worker.LocalWorker(local_worker))
    for build_worker in BuildWorkers:
        if build_worker['type'] == 'default':
            w.append(worker.Worker(build_worker['uuid'], build_worker['password']))
    for node_worker in NodeWorkers:
        if node_worker['type'] == 'node':
            w.append(worker.Worker(node_worker['uuid'], node_worker['password']))
    return w
