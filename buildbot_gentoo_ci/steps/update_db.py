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
        self.project_data = yield self.gentooci.db.projects.getProjectByName(self.gentooci.config.project['project'])
        if self.project_data is None:
            log.err('No data for project in the database')
            return FAILURE
        self.profile_repository_data = yield self.gentooci.db.repositorys.getRepositoryByUuid(self.project_data['profile_repository_uuid'])
        if self.profile_repository_data is None:
            log.err('No data for repository in the database')
            return FAILURE
        print(self.project_data)
        print(self.profile_repository_data)
        print(self.getProperty("git_change"))
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
                            'commit_time' : self.getProperty("git_change")['timestamp'],
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
        change_data = self.getProperty("git_change")
        # check if git_change is a dict
        if not isinstance(change_data, dict):
            return FAILURE
        addStepUpdateCPVData = []
        # make a trigger for all cpv in the list
        for cpv in change_data['cpvs']:
            self.success = True
            if change_data['repository'] != self.getProperty("repository_data")['name']:
                log.msg("%s don't match" % change_data['repository'])
                self.success = False
            # Trigger cpv builds and update db if we are working with ebuilds
            # check that cpv is valied
            if catpkgsplit(cpv) is None:
                log.msg("%s is not vaild package name" % cpv)
                self.success = False
            if self.success:
                revision_data = {}
                revision_data['author'] = change_data['author']
                revision_data['committer']  = change_data['committer']
                revision_data['comments'] = change_data['comments']
                revision_data['revision'] = change_data['revision']
                addStepUpdateCPVData.append(
                    steps.Trigger(
                        schedulerNames=['update_cpv_data'],
                        waitForFinish=False,
                        updateSourceStamp=False,
                        set_properties={
                            'cpv' : cpv,
                            'project_data' : self.getProperty("project_data"),
                            'repository_data' : self.getProperty("repository_data"),
                            'revision_data' : revision_data,
                        }
                    )
                )
        print(addStepUpdateCPVData)
        yield self.build.addStepsAfterCurrentStep(addStepUpdateCPVData)
        if self.success is False:
            return FAILURE
        return SUCCESS
