# Copyright 2022 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from buildbot.plugins import worker, util

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

@util.renderer
def docker_images(props):
    return 'bb-worker-' + props.getProperty('project_uuid') + ':latest'

@util.renderer
def docker_volumes(props):
    volumes_list = []
    #FIXME: set in master.cfg
    src_dir = '/srv/gentoo/portage/' + props.getProperty('project_uuid')
    dest_dir = '/var/cache/portage'
    #add distdir
    volumes_list.append(src_dir + '/distfiles' + ':' + dest_dir + '/distfiles')
    #add bindir
    volumes_list.append(src_dir + '/packages' + ':' + dest_dir + '/packages')
    return volumes_list

def gentoo_workers(worker_data):
    w = []
    g_ci_w = gentoo_ci_workers(worker_data)
    LocalWorkers = g_ci_w.getLocalWorkersUuid()
    BuildWorkers = g_ci_w.getBuildWorkersAllData()
    NodeWorkers = g_ci_w.getNodedWorkersAllData()
    docker_hostconfig = {}
    # For use of sandbox stuff
    # FEATURES="ipc-sandbox network-sandbox pid-sandbox"
    docker_hostconfig['cap_add'] = ['SYS_ADMIN', 'NET_ADMIN', 'SYS_PTRACE']
    # libseccomp overhead
    # https://github.com/seccomp/libseccomp/issues/153
    docker_hostconfig['security_opt'] = ['seccomp=unconfined']
    for local_worker in LocalWorkers:
        w.append(worker.LocalWorker(local_worker))
    for build_worker in BuildWorkers:
        if build_worker['type'] == 'default':
            w.append(worker.Worker(build_worker['uuid'], build_worker['password']))
        #FIXME: set settings in master.cfg
        if build_worker['type'] == 'docker':
            w.append(worker.DockerLatentWorker(build_worker['uuid'],
                            build_worker['password'],
                            docker_host='tcp://192.168.1.3:2375',
                            image=docker_images,
                            volumes=docker_volumes,
                            hostconfig=docker_hostconfig,
                            followStartupLogs=True,
                            masterFQDN='192.168.1.5',
                            build_wait_timeout=3600
                            ))
    for node_worker in NodeWorkers:
        if node_worker['type'] == 'node':
            w.append(worker.Worker(node_worker['uuid'], node_worker['password']))
    return w
