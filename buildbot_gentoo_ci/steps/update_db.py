# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from portage.versions import catpkgsplit

from twisted.internet import defer
from twisted.python import log

from buildbot.process.buildstep import BuildStep
from buildbot.process.results import SUCCESS
from buildbot.process.results import FAILURE
from buildbot.plugins import steps

class GetDataGentooCiProject(BuildStep):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        self.project_data = yield self.gentooci.db.projects.getProjectByName(self.gentooci.config.project['project']['update_db'])
        if self.project_data is None:
            log.err('No data for project in the database')
            return FAILURE
        self.profile_repository_data = yield self.gentooci.db.repositorys.getRepositoryByUuid(self.project_data['profile_repository_uuid'])
        if self.profile_repository_data is None:
            log.err('No data for profile repository in the database')
            return FAILURE
        if not isinstance(self.getProperty("change_data"), dict):
            return FAILURE
        print(self.project_data)
        print(self.profile_repository_data)
        print(self.getProperty("change_data"))
        print(self.getProperty("repository"))
        repository = False
        self.repository_data = False
        if self.getProperty("repository").endswith('.git'):
            for v in self.getProperty("repository").split('/'):
                if v.endswith('.git'):
                    if v[:-4] == 'gentoo-ci':
                        repository = 'gentoo'
                    else:
                        repository = v[:-4]
        if repository:
            self.repository_data = yield self.gentooci.db.repositorys.getRepositoryByName(repository)
        if self.getProperty("change_data")['repository'] != self.repository_data['name']:
            log.msg("%s don't match" % self.getProperty("change_data")['repository'])
            return FAILURE
        self.setProperty("project_data", self.project_data, 'project_data')
        self.setProperty("profile_repository_data", self.profile_repository_data, 'profile_repository_data')
        self.setProperty("repository_data", self.repository_data, 'repository_data')
        return SUCCESS

class TriggerUpdateRepositorys(BuildStep):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    name = 'TriggerUpdateRepositorys'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    @defer.inlineCallbacks
    def run(self):
        yield self.build.addStepsAfterCurrentStep([
            steps.Trigger(
                        schedulerNames=['update_repo_check'],
                        waitForFinish=True,
                        updateSourceStamp=False,
                        set_properties={
                            'profile_repository_uuid' : self.getProperty("profile_repository_data")['uuid'],
                            'repository_uuid' : self.getProperty("repository_data")['uuid'],
                            'commit_time' : self.getProperty("change_data")['timestamp'],
                        }
            )
        ])
        return SUCCESS

class TriggerCheckForCPV(BuildStep):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    name = 'TriggerCheckForCPV'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    @defer.inlineCallbacks
    def run(self):
        yield self.build.addStepsAfterCurrentStep([
            steps.Trigger(
                schedulerNames=['update_cpv_data'],
                waitForFinish=False,
                updateSourceStamp=False,
                set_properties={
                    'project_data' : self.getProperty("project_data"),
                    'repository_data' : self.getProperty("repository_data"),
                    'change_data' : self.getProperty("change_data"),
                }
            )
        ])
        return SUCCESS
