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
        #self.repository = self.getProperty("repository")
        self.repository = 'gentoo'
        self.repository_data = yield self.gentooci.db.repositorys.getRepositoryByName(self.repository)
        print(self.project_data)
        print(self.project_repository_data)
        print(self.profile_repository_data)
        print(self.getProperty("cpv_changes"))
        print(self.repository_data)
        self.setProperty("project_data", self.project_data, 'project_data')
        self.setProperty("project_repository_data", self.project_repository_data, 'project_repository_data')
        self.setProperty("profile_repository_data", self.profile_repository_data, 'profile_repository_data')
        self.setProperty("cpv_changes", self.getProperty("cpv_changes"), 'cpv_changes')
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
        if not success:
            return FAILURE
        self.setProperty("project_data", self.project_data, 'project_data')
        self.setProperty("project_repository_data", self.project_repository_data, 'project_repository_data')
        self.setProperty("cpv_changes", self.getProperty("cpv_changes"), 'cpv_changes')
        self.setProperty("repository_data", self.repository_data, 'repository_data')
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
        self.setProperty("project_data", self.project_data, 'project_data')
        self.setProperty("cpv_changes", self.getProperty("cpv_changes"), 'cpv_changes')
        self.setProperty("repository_data", self.getProperty("repository_data"), 'repository')
        return SUCCESS

class CheckCPVGentooCiProject(BuildStep):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        #self.cpv_changes = self.getProperty("cpv_changes")
        self.cpv_changes = []
        self.cpv_changes.append('dev-python/django-3.1.7')
        self.cpv_changes.append('dev-python/scrypt-0.8.16')
        print(self.cpv_changes)
        print(self.getProperty("repository_data"))
        # check if cpv_change is a string or a list
        if isinstance(self.cpv_changes, list):
            self.cpv_list = self.cpv_changes
        else:
            self.cpv_list = []
            self.cpv_list.append(self.cpv_changes)
        self.success = True
        addStepUpdateCPVData = []
        for cpv in sorted(self.cpv_list):
            # check that cpv is valied
            if catpkgsplit(cpv) is None:
                log.msg("%s is not vaild package name" % cpv)
                self.success = False
            else:
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
                        }
                    )
                )
        yield self.build.addStepsAfterCurrentStep(addStepUpdateCPVData)
        if self.success is False:
            return FAILURE
        return SUCCESS
