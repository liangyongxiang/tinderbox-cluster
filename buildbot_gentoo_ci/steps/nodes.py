# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os
import re
import json
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


from portage.versions import catpkgsplit, cpv_getversion
from portage.dep import dep_getcpv, dep_getslot, dep_getrepo

from twisted.internet import defer
from twisted.python import log

from buildbot.process.buildstep import BuildStep
from buildbot.process.results import SUCCESS
from buildbot.process.results import FAILURE
from buildbot.process.results import SKIPPED
from buildbot.plugins import steps, util

from buildbot_gentoo_ci.steps import portage as portage_steps
from buildbot_gentoo_ci.steps import builders as builders_steps

class SetupPropertys(BuildStep):
    name = 'Setup propertys for stage4 image'
    description = 'Running'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        # we need project uuid and worker uuid
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        project_data = yield self.gentooci.db.projects.getProjectByUuid(self.getProperty('project_uuid'))
        self.setProperty('project_data', project_data, 'project_data')
        #FIXME: set it in db node config
        self.workerbase = yield os.path.join('/', 'srv', 'gentoo', 'stage4')
        self.setProperty('workerbase', self.workerbase, 'workerbase')
        self.setProperty('stage3', 'image', 'stage3')
        # we only support docker for now
        self.setProperty('type', 'docker', 'type')
        return SUCCESS

class SetupStage4Steps(BuildStep):
    name = 'Setup steps for stage4 image'
    description = 'Running'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        self.setProperty('portage_repos_path', self.gentooci.config.project['project']['worker_portage_repos_path'], 'portage_repos_path')
        aftersteps_list = []
        separator = '\n'
        log = yield self.addLog('makeing_stage4')
        if self.getProperty("type") == 'docker':
            print('build this stage4 %s on %s for %s' % (self.getProperty('project_uuid'), self.getProperty('workername'), self.getProperty('project_data')['name']))
            self.descriptionDone = ' '.join(['build this stage4', self.getProperty('project_uuid'), 'on', self.getProperty('workername'), 'for', self.getProperty('project_data')['name']])
            #FIXME: package list should be in the db project
            package_list = ['dev-vcs/git', 'app-text/ansifilter', 'dev-util/pkgcheck', 'dev-lang/rust-bin', 'app-admin/eclean-kernel', 'app-portage/gentoolkit', 'sys-kernel/gentoo-kernel-bin', 'app-editors/nano']
            if 'systemd' or 'openrc' in self.getProperty('project_data')['image']:
                workerdest = yield os.path.join(self.getProperty("workerbase"), self.getProperty('project_uuid'))
                workerdest_etc = yield os.path.join(workerdest, 'etc')
                print(workerdest_etc)
                # create dir
                aftersteps_list.append(steps.ShellCommand(
                        flunkOnFailure=True,
                        name='Create stage4 dir',
                        command=['mkdir', self.getProperty('project_uuid')],
                        workdir=self.getProperty("workerbase")
                        ))
                # download stage3
                aftersteps_list.append(GetSteg3())
                # setup portage
                aftersteps_list.append(builders_steps.UpdateRepos(workdir=workerdest))
                aftersteps_list.append(portage_steps.SetReposConf(workdir=workerdest))
                aftersteps_list.append(portage_steps.SetMakeConf(workdir=workerdest))
                # add localegen
                #FIXME: set that in config
                locale_conf = []
                locale_conf.append('en_US.UTF-8 UTF-8')
                locale_conf.append('en_US ISO-8859-1')
                locale_conf.append('C.UTF8 UTF-8')
                locale_conf_string = separator.join(locale_conf)
                aftersteps_list.append(
                    steps.StringDownload(locale_conf_string + separator,
                                workerdest="locale.gen",
                                workdir=workerdest_etc
                                ))
                yield log.addStdout('File: ' + 'locale.gen' + '\n')
                for line in locale_conf:
                    yield log.addStdout(line + '\n')
                aftersteps_list.append(
                    steps.StringDownload('LANG="en_US.utf8"' + separator,
                                workerdest="locale.conf",
                                workdir=workerdest_etc
                                ))
                yield log.addStdout('Setting LANG to: ' + 'en_US.utf8' + '\n')
                aftersteps_list.append(SetSystemdNspawnConf())
                # run localgen
                aftersteps_list.append(steps.ShellCommand(
                    flunkOnFailure=True,
                    name='Run locale-gen on the chroot',
                    command=['systemd-nspawn', '-D', self.getProperty('project_uuid'), 'locale-gen'],
                    workdir=self.getProperty("workerbase")
                    ))
                # update timezone
                # install packages in world file config
                command_list = ['systemd-nspawn', '-D', self.getProperty('project_uuid'), 'emerge']
                for package in package_list:
                    command_list.append(package)
                aftersteps_list.append(steps.ShellCommand(
                    flunkOnFailure=True,
                    name='Install programs on the chroot',
                    command=command_list,
                    workdir=self.getProperty("workerbase")
                    ))
                # update container
                aftersteps_list.append(steps.ShellCommand(
                    flunkOnFailure=True,
                    name='Run update on the chroot',
                    command=['systemd-nspawn', '-D', self.getProperty('project_uuid'), 'emerge', '--update', '--deep', '--newuse', '@world'],
                    workdir=self.getProperty("workerbase")
                    ))
                # install buildbot-worker
                aftersteps_list.append(steps.ShellCommand(
                    flunkOnFailure=True,
                    name='Install buildbot worker on the chroot',
                    command=['systemd-nspawn', '-D', self.getProperty('project_uuid'), 'emerge', 'buildbot-worker'],
                    workdir=self.getProperty("workerbase")
                    ))
                #FIXME: move this to image build for chroot type part
                if self.getProperty("type") == 'chroot':
                    # set hostname
                    aftersteps_list.append(steps.StringDownload(
                        self.getProperty("worker") + separator,
                        workerdest="hostname",
                        workdir=workerdest_etc
                    ))
                    yield log.addStdout('Setting hostname to: ' + self.getProperty("worker") + '\n')
                    # config buildbot-worker
                    # get password from db if set else generate one in uuid
                    worker_passwd = 'test1234'
                    aftersteps_list.append(steps.ShellCommand(
                        flunkOnFailure=True,
                        SecretString=[worker_passwd, '<WorkerPassword>'],
                        name='Install buildbot worker on the chroot',
                        command=['systemd-nspawn', '-D', self.getProperty('project_uuid'), 'buildbot-worker', 'create-worker', '/var/lib/buildbot_worker', '192.168.1.5', self.getProperty("worker"), worker_passwd],
                        workdir=self.getProperty("workerbase")
                    ))
                if self.getProperty("type") == 'docker':
                    # copy docker_buildbot.tac to worker dir
                    buildbot_worker_config_file = yield os.path.join(self.master.basedir, 'files', 'docker_buildbot_worker.tac')
                    aftersteps_list.append(steps.FileDownload(
                        flunkOnFailure=True,
                        name='Upload buildbot worker config to the stage4',
                        mastersrc=buildbot_worker_config_file,
                        workerdest='var/lib/buildbot_worker/buildbot.tac',
                        workdir=workerdest
                    ))
                # add info to the buildbot worker
                worker_info_list = []
                worker_info_list.append(self.getProperty('project_data')['name'])
                worker_info_list.append(self.getProperty("stage3"))
                worker_info_list.append(self.getProperty("type"))
                #FIXME: worker name of self.getProperty('workername') from node table
                worker_info_list.append('node1')
                print(worker_info_list)
                worker_info = ' '.join(worker_info_list)
                aftersteps_list.append(steps.StringDownload(
                    worker_info + separator,
                    workerdest='var/lib/buildbot_worker/info/host',
                    workdir=workerdest
                ))
                    # if self.getProperty("type") == 'chroot' and 'systemd' in self.getProperty('project_data')['image']:
                    # set buildbot worker to run
                # depclean
                aftersteps_list.append(steps.ShellCommand(
                    flunkOnFailure=True,
                    name='Depclean on the chroot',
                    command=['systemd-nspawn', '-D', self.getProperty('project_uuid'), 'emerge', '--depclean'],
                    workdir=self.getProperty("workerbase")
                    ))
                # remove the gentoo repo
                # compress it
                aftersteps_list.append(steps.ShellCommand(
                    flunkOnFailure=True,
                    name='Compress the stage4',
                    command=['tar', '-cf', '--numeric-owner', self.getProperty('project_uuid') + '.tar', self.getProperty('project_uuid')],
                    workdir=self.getProperty("workerbase")
                ))
                # signing the stage4
                # remove the dir
                aftersteps_list.append(steps.ShellCommand(
                    flunkOnFailure=True,
                    name='Remove the stage4 dir',
                    command=['rm', '-R', self.getProperty('project_uuid')],
                    workdir=self.getProperty("workerbase")
                ))
        if aftersteps_list != []:
            yield self.build.addStepsAfterCurrentStep(aftersteps_list)
        return SUCCESS

class GetSteg3(BuildStep):
    name = 'Get the steg3 image'
    description = 'Running'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        compresstype = '.tar.xz'
        downloadbaseurl = 'https://gentoo.osuosl.org/releases'
        #downloadbaseurl = 'https://bouncer.gentoo.org/fetch/root/all/releases'
        aftersteps_list = []
        project_data = self.getProperty('project_data')
        project_keyword_data = yield self.gentooci.db.keywords.getKeywordById(project_data['keyword_id'])
        keyword = project_keyword_data['name']
        # if the stage3 end with latest we neeed to get the date
        if project_data['image'].endswith('latest'):
            stage3latest = 'latest' + '-' + project_data['image'].replace('-latest', '') + '.txt'
            downloadurllatest = '/'.join([downloadbaseurl, keyword, 'autobuilds', stage3latest])
            print(downloadurllatest)
            session = requests.Session()
            retry = Retry(connect=3, backoff_factor=0.5)
            adapter = HTTPAdapter(max_retries=retry)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            r = session.get(downloadurllatest, timeout=5)
            if r.status_code == requests.codes.ok:
                urltext = r.text.split('\n')[2]
                print(urltext)
                date = urltext.split('/')[0]
                image = urltext.split('/')[1].split(' ')[0]
            else:
                r.raise_for_status()
                return FAILURE
        else:
            image = project_data['image'] + compresstype
            date = project_data['image'].split('-')[-1]
        self.descriptionDone = image
        self.setProperty('stage3', image, 'stage3')
        downloadurlstage3 = '/'.join([downloadbaseurl, keyword, 'autobuilds', date, image])
        print(downloadurlstage3)
        aftersteps_list.append(steps.ShellCommand(
                        flunkOnFailure=True,
                        name='Download the stage3 file',
                        command=['wget', '-N', '-nv', downloadurlstage3],
                        workdir=self.getProperty("workerbase")
                        ))
        aftersteps_list.append(steps.ShellCommand(
                        flunkOnFailure=True,
                        name='Download the stage3 DIGESTS file',
                        command=['wget', '-N', '-nv', downloadurlstage3 + '.asc'],
                        workdir=self.getProperty("workerbase")
                        ))
        #FIXME: validate the stage3 file
        aftersteps_list.append(steps.ShellCommand(
                        flunkOnFailure=True,
                        name='Unpack the stage3 file',
                        command=['tar', 'xpf', image, '--xattrs-include=\'*.*\'', '--numeric-owner', '-C',  self.getProperty('project_uuid')],
                        workdir=self.getProperty("workerbase")
                        ))
        if aftersteps_list != []:
            yield self.build.addStepsAfterCurrentStep(aftersteps_list)
        return SUCCESS

class SetSystemdNspawnConf(BuildStep):

    name = 'SetSystemdNspawnConf'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        nspawn_conf_path = '/etc/systemd/nspawn/'
        log = yield self.addLog(self.getProperty('project_uuid') + '.nspawn')
        #FIXME: set it in config
        separator = '\n'
        nspawn_conf = []
        nspawn_conf.append('[Files]')
        nspawn_conf.append('TemporaryFileSystem=/run/lock')
        # db node config portage cache bind
        nspawn_conf.append('Bind=/srv/gentoo/portage/' + self.getProperty('project_uuid') + ':/var/cache/portage')
        nspawn_conf.append('[Exec]')
        nspawn_conf.append('Capability=CAP_NET_ADMIN')
        nspawn_conf.append('[Network]')
        nspawn_conf.append('VirtualEthernet=no')
        nspawn_conf_string = separator.join(nspawn_conf)
        yield self.build.addStepsAfterCurrentStep([
            steps.StringDownload(nspawn_conf_string + separator,
                                workerdest=self.getProperty('project_uuid') + '.nspawn',
                                workdir=nspawn_conf_path)
            ])
        yield log.addStdout('File: ' + self.getProperty('project_uuid') + '.nspawn' + '\n')
        for line in nspawn_conf:
            yield log.addStdout(line + '\n')
        return SUCCESS
