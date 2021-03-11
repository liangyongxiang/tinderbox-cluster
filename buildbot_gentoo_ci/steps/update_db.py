# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os

from portage import config as portage_config
from portage.versions import catpkgsplit
from portage.util import getconfig

from twisted.internet import defer
from twisted.python import log

from buildbot.process.buildstep import BuildStep
from buildbot.process.results import SUCCESS
from buildbot.process.results import FAILURE
from buildbot.plugins import steps

#from buildbot_gentoo_ci.steps.updatedb_functions import category

class GetDataGentooCiProject(BuildStep):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        self.project_data = yield self.gentooci.db.projects.getProjectByName(self.gentooci.config.project['project'])
        if self.project_data is None:
            log.err('No data for project in the database')
            return FAILURE
        self.project_repository_data = yield self.gentooci.db.repositorys.getRepositoryByUuid(self.project_data['project_repository_uuid'])
        if self.project_repository_data is None:
            log.err('No data for repository in the database')
            return FAILURE
        self.profile_repository_data = yield self.gentooci.db.repositorys.getRepositoryByUuid(self.project_data['profile_repository_uuid'])
        if self.profile_repository_data is None:
            log.err('No data for repository in the database')
            return FAILURE
        print(self.project_data)
        print(self.project_repository_data)
        print(self.profile_repository_data)
        print(self.getProperty("git_changes"))
        print(self.getProperty("repository"))
        repository = False
        self.repository_data = False
        if self.getProperty("repository").endswith('.git'):
            for v in self.getProperty("repository").split('/'):
                if v.endswith('.git'):
                    repository = v[:-4]
        if repository:
            self.repository_data = yield self.gentooci.db.repositorys.getRepositoryByName(repository)
        self.setProperty("project_data", self.project_data, 'project_data')
        self.setProperty("project_repository_data", self.project_repository_data, 'project_repository_data')
        self.setProperty("profile_repository_data", self.profile_repository_data, 'profile_repository_data')
        self.setProperty("repository_data", self.repository_data, 'repository_data')
        return SUCCESS

class CheckPathGentooCiProject(BuildStep):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        self.repository_basedir = self.gentooci.config.project['repository_basedir']
        self.profile_repository_data = self.getProperty("profile_repository_data")
        self.project_repository_data = self.getProperty("project_repository_data")
        self.repository_data = self.getProperty("repository_data")
        self.project_data = self.getProperty("project_data")
        self.project_path = yield os.path.join(self.repository_basedir, self.project_repository_data['name'] + '.git')
        self.repository_path = yield os.path.join(self.repository_basedir, self.repository_data['name'] + '.git')
        self.portage_path = yield os.path.join(self.project_path, self.project_data['name'], 'etc/portage')
        success = True
        for x in [
                  os.path.join(self.repository_basedir, self.profile_repository_data['name'] + '.git'),
                  self.project_path,
                  self.portage_path,
                  os.path.join(self.portage_path, 'make.profile'),
                  self.repository_path
                  # check the path of make.profile is project_data['profile']
                 ]:
            is_dir = True
            if not os.path.isdir(x):
                is_dir  = False
                success = False
            print("isdir(%s): %s" %(x, is_dir))
        print(self.getProperty("builddir"))
        if not success:
            return FAILURE
        return SUCCESS

class CheckProjectGentooCiProject(BuildStep):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        self.repository_basedir = self.gentooci.config.project['repository_basedir']
        self.project_repository_data = self.getProperty("project_repository_data")
        self.project_data = self.getProperty("project_data")
        self.project_path = yield os.path.join(self.repository_basedir, self.project_repository_data['name'] + '.git')
        self.config_root = yield os.path.join(self.project_path, self.project_data['name'], '')
        self.make_conf_file = yield os.path.join(self.config_root, 'etc/portage', '') + 'make.conf'
        try:
            getconfig(self.make_conf_file, tolerant=0, allow_sourcing=True, expand=True)
            mysettings = portage_config(config_root = self.config_root)
            mysettings.validate()
        except ParseError as e:
            print("project portage conf has error %s" %(str(e)))
            return FAILURE
        self.setProperty("config_root", self.config_root, 'config_root')
        return SUCCESS

class CheckCPVGentooCiProject(BuildStep):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.git_changes = self.getProperty("git_changes")
        print(self.git_changes)
        # check if git_change is a string or a list
        if not isinstance(self.git_changes, list):
            return FAILURE
        self.success = True
        addStepUpdateCPVData = []
        for change_data in self.git_changes:
            # make a trigger for all cpv in the list
            for cpv in change_data['cpvs']:
                # check that cpv is valied
                if catpkgsplit(cpv) is None:
                    log.msg("%s is not vaild package name" % cpv)
                    self.success = False
                else:
                    if change_data['repository'] != self.getProperty("repository_data")['name']:
                        log.msg("%s don't match" % change_data['repository'])
                        self.success = False
                    else:
                        revision_data = {}
                        revision_data['author'] = change_data['author']
                        revision_data['committer']  = change_data['committer']
                        revision_data['comments'] = change_data['comments']
                        revision_data['revision'] = change_data['revision']
                        # call update_cpv_data
                        addStepUpdateCPVData.append(
                            steps.Trigger(
                                schedulerNames=['update_cpv_data'],
                                waitForFinish=False,
                                updateSourceStamp=False,
                                set_properties={
                                    'cpv' : cpv,
                                    'config_root' : self.getProperty("config_root"),
                                    'project_data' : self.getProperty("project_data"),
                                    'repository_data' : self.getProperty("repository_data"),
                                    'revision_data' : revision_data,
                                }
                            )
                        )
            yield self.build.addStepsAfterCurrentStep(addStepUpdateCPVData)
        if self.success is False:
            return FAILURE
        return SUCCESS
