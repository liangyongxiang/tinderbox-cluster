# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os

from twisted.internet import defer
from twisted.python import log

from buildbot.process.buildstep import BuildStep
from buildbot.process.results import SUCCESS
from buildbot.process.results import FAILURE
from buildbot.plugins import steps

class TriggerRunBuildRequest(BuildStep):
    
    name = 'TriggerRunBuildRequest'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        yield self.build.addStepsAfterCurrentStep([
                steps.Trigger(
                    schedulerNames=['run_build_request'],
                        waitForFinish=False,
                        updateSourceStamp=False,
                        set_properties={
                            'cpv' : self.getProperty("cpv"),
                            'version_data' : self.getProperty("version_data"),
                            'projectrepository_data' : self.getProperty('projectrepository_data'),
                            'use_data' : self.getProperty("use_data"),
                            'fullcheck' : self.getProperty("fullcheck"),
                        }
                )])
        return SUCCESS

class GetProjectRepositoryData(BuildStep):
    
    name = 'GetProjectRepositoryData'
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
        self.projectrepositorys_data = yield self.gentooci.db.projects.getProjectRepositorysByUuid(self.getProperty("repository_data")['uuid'])
        if self.projectrepositorys_data is None:
            print('No Projects have this %s repository for testing' % self.getProperty("repository_data")['name'])
            return SUCCESS
        # for loop to get all the projects that have the repository
        for projectrepository_data in self.projectrepositorys_data:
            # get project data
            project_data = yield self.gentooci.db.projects.getProjectByUuid(projectrepository_data['project_uuid'])
            # check if auto, enabled and not in config.project['project']
            if project_data['auto'] is True and project_data['enabled'] is True and project_data['name'] != self.gentooci.config.project['project']:
                # set Property projectrepository_data so we can use it in the trigger
                self.setProperty('projectrepository_data', projectrepository_data, 'projectrepository_data')
                self.setProperty('use_data', None, 'use_data')
                # get name o project keyword
                project_keyword_data = yield self.gentooci.db.keywords.getKeywordById(project_data['keyword_id'])
                # if not * (all keywords)
                if project_keyword_data['name'] != '*' or project_data['status'] == 'all':
                    self.setProperty('fullcheck', False, 'fullcheck')
                    # get status of the keyword on cpv
                    version_keywords_data = self.getProperty("version_keyword_dict")[project_keyword_data['name']]
                    # if unstable trigger BuildRequest on cpv
                    if project_data['status'] == version_keywords_data['status']:
                        yield self.build.addStepsAfterCurrentStep([TriggerRunBuildRequest()])
        return SUCCESS

class UpdateProfileRepo(BuildStep):
    
    name = 'UpdateProfileRepo'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        # set this in config
        self.portage_repos_path = '/var/db/repos/'
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        print('build this %s' % self.getProperty("cpv"))
        self.setProperty('portage_repos_path', self.portage_repos_path, 'portage_repos_path')
        projectrepository_data = self.getProperty('projectrepository_data')
        print(projectrepository_data)
        repository_data = yield self.gentooci.db.repositorys.getRepositoryByUuid(projectrepository_data['repository_uuid'])
        project_data = yield self.gentooci.db.projects.getProjectByUuid(projectrepository_data['project_uuid'])
        self.setProperty('project_data', project_data, 'project_data')
        self.profile_repository_data = yield self.gentooci.db.repositorys.getRepositoryByUuid(project_data['profile_repository_uuid'])
        profile_repository_path = yield os.path.join(self.portage_repos_path, self.profile_repository_data['name'])
        yield self.build.addStepsAfterCurrentStep([
            steps.Git(repourl=self.profile_repository_data['mirror_url'],
                            mode='incremental',
                            submodules=True,
                            workdir=os.path.join(profile_repository_path, ''))
            ])
        return SUCCESS

class SetMakeProfile(BuildStep):

    name = 'SetMakeProfile'
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
        portage_repos_path = self.getProperty('portage_repos_path')
        project_data = self.getProperty('project_data')
        profile_repository_data = yield self.gentooci.db.repositorys.getRepositoryByUuid(project_data['profile_repository_uuid'])
        makeprofiles_paths = []
        makeprofiles_data = yield self.gentooci.db.projects.getProjectPortageByUuidAndDirectory(project_data['uuid'], 'make.profile')
        for makeprofile in makeprofiles_data:
            makeprofile_path = yield os.path.join(portage_repos_path, profile_repository_data['name'], 'profiles', makeprofile['value'], '')
            makeprofiles_paths.append('../../..' + makeprofile_path)
        separator = '\n'
        makeprofile_path_string = separator.join(makeprofiles_paths)
        yield self.build.addStepsAfterCurrentStep([
            steps.StringDownload(makeprofile_path_string + separator,
                                workerdest="make.profile/parent",
                                workdir='/etc/portage/')
            ])
        return SUCCESS
