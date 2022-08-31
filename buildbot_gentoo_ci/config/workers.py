# Copyright 2022 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from buildbot.plugins import worker, util

class gentoo_ci_workers():
    def __init__(self, worker_data, **kwargs):
        self.worker_data = worker_data

    def getWorkersUuid(self, worker_type):
        worker_list = []
        for worker in self.worker_data:
            if worker['type'] == worker_type and worker['enable'] is True:
                worker_list.append(worker['uuid'])
        print(worker_list)
        return worker_list

    def getWorkersAllData(self, worker_type):
        worker_list = []
        for worker in self.worker_data:
            if worker['type'] == worker_type and worker['enable'] is True:
                worker_list.append(worker)
        print(worker_list)
        return worker_list

@util.renderer
def build_docker_images(props):
    return 'bb-worker-' + props.getProperty('project_uuid') + ':latest'

@util.renderer
def log_docker_images(props):
    return 'bb-worker-log' + ':latest'

@util.renderer
def docker_volumes(props):
    volumes_list = []
    #FIXME: set in master.cfg /srv/gentoo/portage/
    src_dir = '/srv/gentoo/portage/' + props.getProperty('project_uuid')
    dest_dir = '/var/cache/portage'
    #add distdir
    volumes_list.append(src_dir + '/distfiles' + ':' + dest_dir + '/distfiles')
    #add bindir
    volumes_list.append(src_dir + '/packages' + ':' + dest_dir + '/packages')
    return volumes_list

#NOTE: source permission set to user/group buildbot
@util.renderer
def docker_volumes_repositorys(props):
    volumes_list = []
    #FIXME: set in master.cfg /srv/gentoo/portage/repos
    src_dir = '/srv/gentoo/portage/repos'
    #FIXME: set to getProperty('builddir') + repositorys
    dest_dir = '/var/lib/buildbot_worker/repositorys'
    #add distdir
    volumes_list.append(':'.join([src_dir, dest_dir]))
    return volumes_list

def gentoo_workers(worker_data):
    w = []
    g_ci_w = gentoo_ci_workers(worker_data)

    for local_worker in g_ci_w.getWorkersUuid('local'):
        w.append(worker.LocalWorker(local_worker))
    for node_worker in g_ci_w.getWorkersAllData('node'):
        w.append(worker.Worker(node_worker['uuid'], node_worker['password']))
    # docker workers
    docker_hostconfig = {}
    # For use of sandbox stuff
    # FEATURES="ipc-sandbox network-sandbox pid-sandbox"
    docker_hostconfig['cap_add'] = ['SYS_ADMIN', 'NET_ADMIN', 'SYS_PTRACE']
    # libseccomp overhead
    # https://github.com/seccomp/libseccomp/issues/153
    docker_hostconfig['security_opt'] = ['seccomp=unconfined']
    for build_worker in g_ci_w.getWorkersAllData('docker'):
        #FIXME: set settings in master.cfg
        if build_worker['type'] == 'docker':
            w.append(worker.DockerLatentWorker(build_worker['uuid'],
                            build_worker['password'],
                            docker_host='tcp://127.0.0.1:2375',
                            image=build_docker_images,
                            volumes=docker_volumes,
                            hostconfig=docker_hostconfig,
                            followStartupLogs=True,
                            masterFQDN='127.0.0.1',
                            build_wait_timeout=3600
                            ))
    for log_worker in g_ci_w.getWorkersAllData('log'):
        #FIXME: set settings in master.cfg
        if log_worker['type'] == 'log':
            w.append(worker.DockerLatentWorker(log_worker['uuid'],
                            log_worker['password'],
                            docker_host='tcp://127.0.0.1:2375',
                            image=log_docker_images,
                            volumes=docker_volumes_repositorys,
                            hostconfig=docker_hostconfig,
                            followStartupLogs=True,
                            masterFQDN='192.168.1.5',
                            #build_wait_timeout=3600
                            ))
    return w
