# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os
import pygit2

from portage import config as portage_config
from portage.versions import catpkgsplit
from portage.util import getconfig

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
        self.setProperty("profile_repository_data", self.profile_repository_data, 'profile_repository_data')
        self.setProperty("repository_data", self.repository_data, 'repository_data')
        return SUCCESS

class CheckPath(BuildStep):

    name = 'CheckPath'
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
        self.repository_basedir = self.gentooci.config.project['repository_basedir']
        self.portage_path = 'portage'
        self.profile_path = yield os.path.join(self.portage_path, 'make.profile')
        self.repos_path = yield os.path.join(self.portage_path, 'repos.conf')
        print(os.getcwd())
        print(self.getProperty("builddir"))
        yield os.chdir(self.getProperty("builddir"))
        success = True
        print(os.getcwd())
        for x in [
                  self.profile_path,
                  self.repos_path,
                  self.repository_basedir
                 ]:
            if not os.path.isdir(x):
                os.makedirs(x)
        return SUCCESS

class UpdateRepos(BuildStep):

    name = 'UpdateRepos'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Origin: https://github.com/MichaelBoselowitz/pygit2-examples/blob/master/examples.py#L54
    # Modifyed by Gentoo Authors.
    @defer.inlineCallbacks
    def gitPull(self, repo, remote_name='origin', branch='master'):
        for remote in repo.remotes:
            if remote.name == remote_name:
                yield remote.fetch()
                remote_master_id = yield repo.lookup_reference('refs/remotes/origin/%s' % (branch)).target
                merge_result, _ = yield repo.merge_analysis(remote_master_id)
                # Up to date, do nothing
                if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
                    return
                # We can just fastforward
                elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
                    yield repo.checkout_tree(repo.get(remote_master_id))
                    try:
                        master_ref = yield repo.lookup_reference('refs/heads/%s' % (branch))
                        yield master_ref.set_target(remote_master_id)
                    except KeyError:
                        yield repo.create_branch(branch, repo.get(remote_master_id))
                    yield repo.head.set_target(remote_master_id)
                elif merge_result & pygit2.GIT_MERGE_ANALYSIS_NORMAL:
                    yield repo.merge(remote_master_id)

                    if repo.index.conflicts is not None:
                        for conflict in repo.index.conflicts:
                            print('Conflicts found in:', conflict[0].path)
                        raise AssertionError('Conflicts, ahhhhh!!')

                    user = yield repo.default_signature
                    tree = yield repo.index.write_tree()
                    commit = yield repo.create_commit('HEAD',
                                            user,
                                            user,
                                            'Merge!',
                                            tree,
                                            [repo.head.target, remote_master_id])
                    # We need to do this or git CLI will think we are still merging.
                    yield repo.state_cleanup()
                else:
                    raise AssertionError('Unknown merge analysis result')

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        self.repository_basedir = self.gentooci.config.project['repository_basedir']
        self.profile_repository_path = yield os.path.join(self.repository_basedir, self.getProperty("profile_repository_data")['name'])
        repo_path = yield pygit2.discover_repository(self.profile_repository_path)
        print(repo_path)
        if repo_path is None:
            yield pygit2.clone_repository(self.getProperty("profile_repository_data")['mirror_url'], self.profile_repository_path)
        else:
            repo = yield pygit2.Repository(repo_path)
            yield self.gitPull(repo)
        if self.getProperty("profile_repository_data")['name'] != self.getProperty("repository_data")['name']:
            self.repository_path = yield os.path.join(self.repository_basedir, self.getProperty("repository_data")['name'])
            repo_path = yield pygit2.discover_repository(self.repository_path)
            if repo_path is None:
                yield pygit2.clone_repository(self.getProperty("profile_repository_data")['mirror_url'], self.repository_path)
            else:
                repo = yield pygit2.Repository(repo_path)
                yield self.gitPull(repo)
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
