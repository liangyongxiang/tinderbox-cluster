# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os
import git
from pathlib import Path

from twisted.internet import defer

from buildbot.process.buildstep import BuildStep
from buildbot.process.results import SUCCESS
from buildbot.process.results import FAILURE
from buildbot.process.results import SKIPPED
from buildbot.plugins import steps, util
from buildbot.config import error as config_error

class CheckPathRepositoryLocal(BuildStep):

    name = 'CheckPathRepositoryLocal'
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
        self.repository_basedir_db = yield os.path.join(self.master.basedir, 'repositorys')
        print(self.repository_basedir_db)
        print(self.gentooci.config.project['repository_basedir'])
        p = Path(self.repository_basedir_db)
        self.setProperty("repository_basedir_db", self.repository_basedir_db, 'repository_basedir_db')
        log = yield self.addLog('CheckPathRepositoryLocal')
        if not Path(self.repository_basedir_db).is_dir():
            yield log.addStdout(' '.join(['Missing link', self.repository_basedir_db]))
            p.symlink_to(self.gentooci.config.project['repository_basedir'])
            yield log.addStdout(' '.join(['Makeing missing link', 'repositorys', 'to', self.gentooci.config.project['repository_basedir']]))
        return SUCCESS

class CheckRepository(BuildStep):

    name = 'CheckRepository'
    description = 'Running'
    descriptionDone = 'Ran'
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, step=None, **kwargs):
        self.step = step
        super().__init__(**kwargs)

    # Origin: https://github.com/MichaelBoselowitz/pygit2-examples/blob/master/examples.py#L54
    # Modifyed by Gentoo Authors.
    def gitPull(self, repo, remote_name='origin', branch='master'):
        for remote in repo.remotes:
            if remote.name == remote_name:
                remote.fetch()
                remote_master_id = repo.lookup_reference('refs/remotes/origin/%s' % (branch)).target
                print(remote_master_id)
                merge_result, _ = repo.merge_analysis(remote_master_id)
                print(merge_result)
                # Up to date, do nothing
                if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
                    print('UP_TO_DATE')
                    return None
                # We can just fastforward
                elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
                    print('FASTFORWARD')
                    repo.checkout_tree(repo.get(remote_master_id))
                    try:
                        master_ref = repo.lookup_reference('refs/heads/%s' % (branch))
                        master_ref.set_target(remote_master_id)
                    except KeyError:
                        repo.create_branch(branch, repo.get(remote_master_id))
                    repo.head.set_target(remote_master_id)
                    return True
                elif merge_result & pygit2.GIT_MERGE_ANALYSIS_NORMAL:
                    print('NORMAL')
                    repo.merge(remote_master_id)
                    if repo.index.conflicts is not None:
                        for conflict in repo.index.conflicts:
                            print('Conflicts found in:', conflict[0].path)
                        raise AssertionError('Conflicts, ahhhhh!!')

                    user = repo.default_signature
                    tree = repo.index.write_tree()
                    commit = repo.create_commit('HEAD',
                                            user,
                                            user,
                                            'Merge!',
                                            tree,
                                            [repo.head.target, remote_master_id])
                    # We need to do this or git CLI will think we are still merging.
                    repo.state_cleanup()
                    return True
                else:
                    raise AssertionError('Unknown merge analysis result')
        return True

    @defer.inlineCallbacks
    def setchmod(self, path):
        for root, dirs, files in os.walk(path):
            for d in dirs:
                yield os.chmod(os.path.join(root, d), 0o0755)
            for f in files:
                yield os.chmod(os.path.join(root, f), 0o0644)

    @defer.inlineCallbacks
    def checkRepos(self, repository_data):
        success = False
        repository_path = yield os.path.join(self.getProperty("repository_basedir_db"), repository_data['name'])
        try:
            repo = git.Repo(repository_path)
        except:
            try:
                yield git.Repo.clone_from(repository_data['url'], repository_path)
            except:
                pass
            else:
                repo = git.Repo(repository_path)
                success = True
        else:
            print('repo commit id to check')
            print(self.getProperty("revision"))
            try:
                commits = list(repo.iter_commits(rev=self.getProperty("revision"), max_count=2))
            except:
                try:
                    yield repo.git.pull()
                except:
                    pass
                else:
                    success = True
            else:
                print('repo allready has commit id')
                print(commits[0].hexsha)
                return None
        if success:
            headcommit = repo.head.commit
            print('repo updated to commit id')
            print(headcommit.hexsha)
        # chmod needed for ebuilds metadata portage.GetAuxMetadata step
        # yield self.setchmod(repository_path)
        return success

    @defer.inlineCallbacks
    def run(self):
        #FIXME: # move som of it to buildfactory update_repo_check
        if self.step == 'profile':
            if self.getProperty("profile_repository_uuid") == self.getProperty("repository_uuid"):
                return SKIPPED
            repository_uuid = self.getProperty("profile_repository_uuid")
        else:
            repository_uuid = self.getProperty("repository_uuid")
        #---
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        repository_data = yield self.gentooci.db.repositorys.getRepositoryByUuid(repository_uuid)
        self.descriptionSuffix = repository_data['name']
        #self.Poller_data = yield self.gentooci.db.repositorys.getGitPollerByUuid(repository_uuid)
        success = yield self.checkRepos(repository_data)
        if success is None:
            return SKIPPED
        if not success:
            return FAILURE
        #yield self.gentooci.db.repositorys.updateGitPollerTime(repository_uuid)
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

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        portage_repos_path = self.getProperty('portage_repos_path')
        project_data = self.getProperty('project_data')
        # update/add all repos that in project_repository for the project
        projects_repositorys_data = yield self.gentooci.db.projects.getRepositorysByProjectUuid(project_data['uuid'])
        for project_repository_data in projects_repositorys_data:
            repository_data = yield self.gentooci.db.repositorys.getRepositoryByUuid(project_repository_data['repository_uuid'])
            print(repository_data)
            if repository_data['auto'] and repository_data['enabled']:
                if self.getProperty('rootworkdir'):
                    repository_path = os.path.join(self.getProperty('rootworkdir'), portage_repos_path[1:], repository_data['name'])
                else:
                    repository_path = os.path.join(portage_repos_path, repository_data['name'], '')
                if repository_data['branch']:
                    branch = repository_data['branch']
                else:
                    branch = 'HEAD'
                # filenames to use with Secret
                if repository_data['sshprivatekey']:
                    sshprivatekey = util.Secret(repository_data['sshprivatekey'])
                    sshhostkey = util.Secret(repository_data['sshhostkey'])
                else:
                    sshprivatekey = None
                    sshhostkey = None
                GitdescriptionDone = ' '.join([repository_data['type'], 'pull',  repository_data['name'], branch])
                if repository_data['type'] == 'git':
                    yield self.build.addStepsAfterCurrentStep([
                        steps.Git(repourl=repository_data['url'],
                            name = 'RunGit',
                            descriptionDone=GitdescriptionDone,
                            branch = branch,
                            mode=repository_data['mode'],
                            method=repository_data['method'],
                            submodules=True,
                            alwaysUseLatest=repository_data['alwaysuselatest'],
                            workdir=repository_path,
                            sshPrivateKey = sshprivatekey,
                            sshHostKey = sshhostkey
                            )
                    ])
                if repository_data['type'] =='gitlab':
                    yield self.build.addStepsAfterCurrentStep([
                        steps.GitLab(repourl=repository_data['url'],
                            name = 'RunGit',
                            descriptionDone=GitdescriptionDone,
                            branch = branch,
                            mode=repository_data['mode'],
                            method=repository_data['method'],
                            submodules=True,
                            alwaysUseLatest=repository_data['alwaysuselatest'],
                            workdir=repository_path,
                            sshPrivateKey = sshprivatekey,
                            sshHostKey = sshhostkey
                            )
                    ])
        return SUCCESS
