# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os
import re

from twisted.internet import defer
from twisted.python import log

from buildbot.process.buildstep import BuildStep
from buildbot.process.results import SUCCESS
from buildbot.process.results import FAILURE
from buildbot.plugins import steps

def PersOutputOfEmerge(rc, stdout, stderr):
    emerge_output = {}
    emerge_output['rc'] = rc
    emerge_output['preserved_libs'] = False
    emerge_output['depclean'] = False
    package_dict = {}
    print(stderr)
    # split the lines
    for line in stdout.split('\n'):
        # package list
        subdict = {}
        if line.startswith('[ebuild') or line.startswith('[binary'):
            # if binaries
            if line.startswith('[ebuild'):
                subdict['binary'] = False
            else:
                subdict['binary'] = True
            # action [ N ] stuff
            subdict['action'] = line[8:15].replace(' ', '')
            # cpv
            cpv_split = re.search('] (.+?) ', line).group(1).split(':')
            cpv = cpv_split[0]
            # repository
            # slot
            if cpv_split[1] == '':
                subdict['slot'] = None
                subdict['repository'] = cpv_split[2]
            else:
                subdict['slot'] = cpv_split[1]
                subdict['repository'] = cpv_split[3]
            # if action U version cpv
            if 'U' in subdict['action']:
                subdict['old_version'] = re.search(' \[(.+?)] ', line).group(1).split(':')
            else:
                subdict['old_version'] = None
            # Use list
            if 'USE=' in line:
                subdict['use'] = re.search('USE="(.+?)" ', line).group(1).split(' ')
            else:
                subdict['use'] = None
            # PYTHON_TARGETS list
            if 'PYTHON_TARGETS=' in line:
                subdict['python_targets'] = re.search('PYTHON_TARGETS="(.+?)" ', line).group(1).split(' ')
            else:
                subdict['python_targets'] = None
            # CPU_FLAGS_X86 list
            package_dict[cpv] = subdict
        if line.startswith('>>>'):
            #FIXME: Handling of >>> output
            pass
        if line.startswith('!!!'):
            #FIXME: Handling of !!! output
            if line.startswith('!!! existing preserved libs'):
                pass
        #FIXME: Handling of depclean output dict of packages that get removed or saved
    # split the lines
    #FIXME: Handling of stderr output
    for line in stderr.split('\n'):
        pass
    return {
        'emerge_output' : emerge_output
        }

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

class SetupPropertys(BuildStep):
    
    name = 'SetupPropertys'
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
        project_data = yield self.gentooci.db.projects.getProjectByUuid(projectrepository_data['project_uuid'])
        self.setProperty('project_data', project_data, 'project_data')
        self.setProperty('preserved_libs', False, 'preserved-libs')
        self.setProperty('depclean', False, 'depclean')
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
        makeprofiles_data = yield self.gentooci.db.projects.getAllProjectPortageByUuidAndDirectory(project_data['uuid'], 'make.profile')
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

class SetReposConf(BuildStep):

    name = 'SetReposConf'
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
        # setup the default.conf
        repos_conf_data = yield self.gentooci.db.projects.getProjectPortageByUuidAndDirectory(project_data['uuid'], 'repos.conf')
        if repos_conf_data is None:
            print('Default repo is not set in repos.conf')
            return FAILURE
        # check if repos_conf_data['value'] is vaild repo name
        separator = '\n'
        default_conf = []
        default_conf.append('[DEFAULT]')
        default_conf.append('main-repo = ' + repos_conf_data['value'])
        default_conf.append('auto-sync = no')
        default_conf_string = separator.join(default_conf)
        yield self.build.addStepsAfterCurrentStep([
            steps.StringDownload(default_conf_string + separator,
                                workerdest="repos.conf/default.conf",
                                workdir='/etc/portage/')
            ])
        # add all repos that project have in projects_repositorys to repos.conf/reponame.conf
        projects_repositorys_data = yield self.gentooci.db.projects.getRepositorysByProjectUuid(project_data['uuid'])
        for project_repository_data in projects_repositorys_data:
            repository_data = yield self.gentooci.db.repositorys.getRepositoryByUuid(project_repository_data['repository_uuid'])
            repository_path = yield os.path.join(portage_repos_path, repository_data['name'])
            repository_conf = []
            repository_conf.append('[' + repository_data['name'] + ']')
            repository_conf.append('location = ' + repository_path)
            repository_conf.append('sync-uri = ' + repository_data['mirror_url'])
            repository_conf.append('sync-type = git')
            repository_conf.append('auto-sync = no')
            repository_conf_string = separator.join(repository_conf)
            yield self.build.addStepsAfterCurrentStep([
                steps.StringDownload(repository_conf_string + separator,
                                workerdest='repos.conf/' + repository_data['name'] + '.conf',
                                workdir='/etc/portage/')
                ])
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
            repository_path = yield os.path.join(portage_repos_path, repository_data['name'])
            yield self.build.addStepsAfterCurrentStep([
            steps.Git(repourl=repository_data['mirror_url'],
                            mode='incremental',
                            submodules=True,
                            workdir=os.path.join(repository_path, ''))
            ])
        return SUCCESS

class SetMakeConf(BuildStep):

    name = 'SetMakeConf'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        #FIXME: Make a dict before we pass it to the make.conf
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        project_data = self.getProperty('project_data')
        makeconf_variables_data = yield self.gentooci.db.portages.getVariables()
        separator1 = '\n'
        separator2 = ' '
        makeconf_list = []
        for k in makeconf_variables_data:
            makeconf_variables_values_data = yield self.gentooci.db.projects.getProjectMakeConfById(project_data['uuid'], k['id'])
            makeconf_variable_list = []
            # we add some default values
            #FIXME:
            # we could set them in a config variables
            # FEATURES
            if k['variable'] == 'FEATURES':
                makeconf_variable_list.append('xattr')
                makeconf_variable_list.append('cgroup')
                makeconf_variable_list.append('-news')
                makeconf_variable_list.append('-collision-protect')
            # EMERGE_DEFAULT_OPTS
            if k['variable'] == 'EMERGE_DEFAULT_OPTS':
                makeconf_variable_list.append('--buildpkg=y')
                makeconf_variable_list.append('--rebuild-if-new-rev=y')
                makeconf_variable_list.append('--rebuilt-binaries=y')
                makeconf_variable_list.append('--usepkg=y')
                makeconf_variable_list.append('--binpkg-respect-use=y')
                makeconf_variable_list.append('--binpkg-changed-deps=y')
                makeconf_variable_list.append('--nospinner')
                makeconf_variable_list.append('--color=n')
                makeconf_variable_list.append('--ask=n')
            # CFLAGS
            if k['variable'] == 'CFLAGS' or k['variable'] == 'FCFLAGS':
                makeconf_variable_list.append('-O2')
                makeconf_variable_list.append('-pipe')
                makeconf_variable_list.append('-march=native')
                makeconf_variable_list.append('-fno-diagnostics-color')
                #FIXME:
                # Depend on worker we may have to add a diffrent march
            if k['variable'] == 'CXXFLAGS':
                makeconf_variable_list.append('${CFLAGS}')
            if k['variable'] == 'FFLAGS':
                makeconf_variable_list.append('${FCFLAGS}')
            if k['variable'] == 'ACCEPT_PROPERTIES':
                makeconf_variable_list.append('-interactive')
            if k['variable'] == 'ACCEPT_RESTRICT':
                makeconf_variable_list.append('-fetch')
            for v in makeconf_variables_values_data:
                if v['build_id'] == 0:
                    makeconf_variable_list.append(v['value'])
            if k['variable'] == 'ACCEPT_LICENSE' and makeconf_variable_list != []:
                makeconf_variable_list.append('ACCEPT_LICENSE="*"')
            if makeconf_variable_list != []:
                makeconf_variable_string = k['variable'] + '="' + separator2.join(makeconf_variable_list) + '"'
                makeconf_list.append(makeconf_variable_string)
        # add hardcoded variables and values
        #FIXME:
        # we could set them in a config variables
        makeconf_list.append('LC_MESSAGES=C')
        makeconf_list.append('NOCOLOR="true"')
        makeconf_list.append('GCC_COLORS=""')
        makeconf_list.append('PORTAGE_TMPFS="/dev/shm"')
        makeconf_list.append('CLEAN_DELAY=0')
        makeconf_list.append('NOCOLOR=true')
        makeconf_list.append('PORT_LOGDIR="/var/cache/portage/logs"')
        makeconf_list.append('PKGDIR="/var/cache/portage/packages"')
        makeconf_list.append('PORTAGE_ELOG_CLASSES="qa"')
        makeconf_list.append('PORTAGE_ELOG_SYSTEM="save"')
        # add ACCEPT_KEYWORDS from the project_data info
        keyword_data = yield self.gentooci.db.keywords.getKeywordById(project_data['keyword_id'])
        if project_data['status'] == 'unstable':
            makeconf_keyword = '~' + keyword_data['name']
        else:
            makeconf_keyword = keyword_data['name']
        makeconf_list.append('ACCEPT_KEYWORDS="' + makeconf_keyword + '"')
        makeconf_string = separator1.join(makeconf_list)
        print(makeconf_string)
        yield self.build.addStepsAfterCurrentStep([
            steps.StringDownload(makeconf_string + separator1,
                                workerdest="make.conf",
                                workdir='/etc/portage/')
            ])
        return SUCCESS

class RunEmerge(BuildStep):

    name = 'RunEmerge'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, step=None,**kwargs):
        self.step = step
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        project_data = self.getProperty('project_data')
        projects_emerge_options = yield self.gentooci.db.projects.getProjectEmergeOptionsByUuid(project_data['uuid'])
        shell_commad_list = [
                    'emerge',
                    '-v'
                    ]
        aftersteps_list = []
        if self.step == 'pre-update':
            shell_commad_list.append('-uDN')
            shell_commad_list.append('--changed-deps')
            shell_commad_list.append('--changed-use')
            shell_commad_list.append('--pretend')
            shell_commad_list.append('@world')
            aftersteps_list.append(
                steps.SetPropertyFromCommandNewStyle(
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=PersOutputOfEmerge,
                        workdir='/'
                ))
            aftersteps_list.append(CheckEmergeLogs('pre-update'))

        if self.step == 'update':
            shell_commad_list.append('-uDNq')
            shell_commad_list.append('--changed-deps')
            shell_commad_list.append('--changed-use')
            shell_commad_list.append('@world')
            aftersteps_list.append(
                steps.SetPropertyFromCommandNewStyle(
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=PersOutputOfEmerge,
                        workdir='/',
                        timeout=None
                ))
            aftersteps_list.append(CheckEmergeLogs('update'))

        if self.step == 'preserved-libs' and self.getProperty('preserved_libs'):
            shell_commad_list.append('-q')
            shell_commad_list.append('@preserved-rebuild')
            aftersteps_list.append(
                steps.SetPropertyFromCommandNewStyle(
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=PersOutputOfEmerge,
                        workdir='/',
                        timeout=None
                ))
            aftersteps_list.append(CheckEmergeLogs('preserved-libs'))
            self.setProperty('preserved_libs', False, 'preserved-libs')

        if self.step == 'pre-depclean' and projects_emerge_options['depclean']:
            shell_commad_list.append('--pretend')
            shell_commad_list.append('--depclean')
            aftersteps_list.append(
                steps.SetPropertyFromCommandNewStyle(
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=PersOutputOfEmerge,
                        workdir='/'
                ))
            aftersteps_list.append(CheckEmergeLogs('depclean'))
            self.setProperty('depclean', False, 'depclean')

        if self.step == 'depclean' and self.getProperty('depclean') and projects_emerge_options['depclean']:
            shell_commad_list.append('-q')
            shell_commad_list.append('--depclean')
            aftersteps_list.append(
                steps.SetPropertyFromCommandNewStyle(
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=PersOutputOfEmerge,
                        workdir='/'
                ))
            aftersteps_list.append(CheckEmergeLogs('depclean'))
        if not self.step is None:
            yield self.build.addStepsAfterCurrentStep(aftersteps_list)
        return SUCCESS

class CheckEmergeLogs(BuildStep):

    name = 'CheckLogs'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, step=None,**kwargs):
        self.step = step
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        project_data = self.getProperty('project_data')
        projects_emerge_options = yield self.gentooci.db.projects.getProjectEmergeOptionsByUuid(project_data['uuid'])
        emerge_output = self.getProperty('emerge_output')
        shell_commad_list = [
                    'emerge',
                    '-v'
                    ]
        aftersteps_list = []

        #FIXME: Prosees the logs and do stuff
        # preserved-libs
        if emerge_output['preserved_libs'] and projects_emerge_options['preserved_libs']:
            self.setProperty('preserved_libs', True, 'preserved-libs')
        # depclean
        # FIXME: check if don't remove needed stuff.
        if emerge_output['depclean'] and projects_emerge_options['depclean']:
            self.setProperty('depclean', True, 'depclean')

        if not self.step is None:
            yield self.build.addStepsAfterCurrentStep(aftersteps_list)
        return SUCCESS
