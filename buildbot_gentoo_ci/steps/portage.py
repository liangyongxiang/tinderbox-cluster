# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os
import io
from pathlib import Path

from portage import config as portage_config
from portage import auxdbkeys
from portage import _encodings
from portage import _unicode_encode
from portage import _parse_eapi_ebuild_head, eapi_is_supported
from portage.versions import cpv_getversion, pkgsplit, catpkgsplit
from portage import portdbapi

from twisted.internet import defer
from twisted.python import log

from buildbot.process.buildstep import BuildStep
from buildbot.process.results import SUCCESS
from buildbot.process.results import FAILURE
from buildbot.process.results import SKIPPED
from buildbot.process import remotecommand
from buildbot.plugins import steps

from buildbot_gentoo_ci.steps import master as master_steps
from buildbot_gentoo_ci.utils.use import getIUseValue

@defer.inlineCallbacks
def WriteTextToFile(path, text_list):
    separator = '\n'
    text_string = separator.join(text_list)
    with open(path, "a") as f:
        yield f.write(text_string)
        yield f.write(separator)
        yield f.close

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
        #NOTE: pkgcheck don't support make.profile as a dir
        # we only support one line in db
        makeprofiles_data = yield self.gentooci.db.projects.getAllProjectPortageByUuidAndDirectory(project_data['uuid'], 'make.profile')
        for makeprofile in makeprofiles_data:
            makeprofile_path = yield os.path.join(portage_repos_path, profile_repository_data['name'], 'profiles', makeprofile['value'], '')
        #    makeprofiles_paths.append('../../..' + makeprofile_path)
        #separator = '\n'
        #makeprofile_path_string = separator.join(makeprofiles_paths)
        # yield self.build.addStepsAfterCurrentStep([
        #    steps.StringDownload(makeprofile_path_string + separator,
        #                        workerdest="make.profile/parent",
        #                        workdir='/etc/portage/')
        #    ])
        #NOTE: pkgcheck profile link
        shell_commad_list = [
                    'ln',
                    '-s'
                    ]
        if self.getProperty('rootworkdir'):
            symlink_makeprofile_path = yield os.path.join(self.getProperty('rootworkdir'), 'etc/portage/make.profile')
        else:
            symlink_makeprofile_path = '/etc/portage/make.profile'
        shell_commad_list.append(makeprofile_path)
        shell_commad_list.append(symlink_makeprofile_path)
        yield self.build.addStepsAfterCurrentStep([
            steps.ShellCommand(
                        command=shell_commad_list,
                        workdir='/'
                )
            ])
        log = yield self.addLog('make.profile')
        yield log.addStdout('Profile path: ' + makeprofile_path + '\n')
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
        if self.getProperty('rootworkdir'):
            portage_etc_path = yield os.path.join(self.getProperty('rootworkdir'), 'etc/portage/')
        else:
            portage_etc_path = '/etc/portage/'
        # setup the default.conf
        repos_conf_data = yield self.gentooci.db.projects.getProjectPortageByUuidAndDirectory(project_data['uuid'], 'repos.conf')
        if repos_conf_data is None:
            print('Default repo is not set in repos.conf')
            return FAILURE
        self.aftersteps_list = []
        # check if we have the dir
        cmd = remotecommand.RemoteCommand('stat', {'file': portage_etc_path + 'repos.conf'})
        yield self.runCommand(cmd)
        if cmd.didFail():
            self.aftersteps_list.append(steps.MakeDirectory(dir="repos.conf",
                                workdir=portage_etc_path))
        log = yield self.addLog('repos.conf')
        # check if repos_conf_data['value'] is vaild repo name
        separator = '\n'
        default_conf = []
        default_conf.append('[DEFAULT]')
        default_conf.append('main-repo = ' + repos_conf_data['value'])
        default_conf.append('auto-sync = no')
        default_conf_string = separator.join(default_conf)
        self.aftersteps_list.append(
            steps.StringDownload(default_conf_string + separator,
                                workerdest="repos.conf/default.conf",
                                workdir=portage_etc_path)
            )
        # display the default.conf
        yield log.addStdout('File: ' + 'default.conf' + '\n')
        for line in default_conf:
            yield log.addStdout(line + '\n')
        # add all repos that project have in projects_repositorys to repos.conf/reponame.conf
        projects_repositorys_data = yield self.gentooci.db.projects.getRepositorysByProjectUuid(project_data['uuid'])
        for project_repository_data in projects_repositorys_data:
            repository_data = yield self.gentooci.db.repositorys.getRepositoryByUuid(project_repository_data['repository_uuid'])
            repository_path = yield os.path.join(portage_repos_path, repository_data['name'])
            repository_conf = []
            repository_conf.append('[' + repository_data['name'] + ']')
            repository_conf.append('location = ' + repository_path)
            repository_conf.append('sync-uri = ' + repository_data['url'])
            repository_conf.append('sync-type = git')
            repository_conf.append('auto-sync = no')
            repository_conf_string = separator.join(repository_conf)
            filename = repository_data['name'] + '.conf'
            self.aftersteps_list.append(
                steps.StringDownload(repository_conf_string + separator,
                                workerdest='repos.conf/' + filename,
                                workdir=portage_etc_path)
                )
            yield log.addStdout('File: ' + filename + '\n')
            for line in repository_conf:
                yield log.addStdout(line + '\n')
        yield self.build.addStepsAfterCurrentStep(self.aftersteps_list)
        return SUCCESS

class SetMakeConf(BuildStep):

    name = 'SetMakeConf'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, workdir=False, **kwargs):
        self.rootworkdir = workdir
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        #FIXME: Make a dict before we pass it to the log
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        project_data = self.getProperty('project_data')
        makeconf_variables_data = yield self.gentooci.db.portages.getVariables()
        if self.getProperty('rootworkdir'):
            portage_etc_path = yield os.path.join(self.getProperty('rootworkdir'), 'etc/portage/')
        else:
            portage_etc_path = '/etc/portage/'
        separator1 = '\n'
        separator2 = ' '
        makeconf_list = []
        log = yield self.addLog('make.conf')
        for k in makeconf_variables_data:
            makeconf_variables_values_data = yield self.gentooci.db.projects.getProjectMakeConfById(project_data['uuid'], k['id'])
            makeconf_variable_list = []
            # CFLAGS
            if k['variable'] == 'CFLAGS' or k['variable'] == 'FCFLAGS':
                makeconf_variable_list.append('-O2')
                makeconf_variable_list.append('-pipe')
                makeconf_variable_list.append('-fno-diagnostics-color')
                #FIXME:
                # Depend on worker we may have to add a diffrent march
                #makeconf_variable_list.append('-march=native')
            if k['variable'] == 'CXXFLAGS':
                makeconf_variable_list.append('${CFLAGS}')
            if k['variable'] == 'FFLAGS':
                makeconf_variable_list.append('${FCFLAGS}')
            # Add default setting if use_default
            if project_data['use_default']:
                default_project_data = yield self.gentooci.db.projects.getProjectByName(self.gentooci.config.project['project']['update_db'])
                default_makeconf_variables_values_data = yield self.gentooci.db.projects.getProjectMakeConfById(default_project_data['uuid'], k['id'])
                for v in default_makeconf_variables_values_data:
                    if v['build_id'] == 0:
                        makeconf_variable_list.append(v['value'])
            for v in makeconf_variables_values_data:
                if v['build_id'] == 0:
                    makeconf_variable_list.append(v['value'])
            #NOTE: set it by project
            #if k['variable'] == 'ACCEPT_LICENSE' and makeconf_variable_list != []:
            #    makeconf_variable_list.append('ACCEPT_LICENSE="*"')
            if makeconf_variable_list != []:
                makeconf_variable_string = k['variable'] + '="' + separator2.join(makeconf_variable_list) + '"'
                makeconf_list.append(makeconf_variable_string)
        # add hardcoded variables from config file
        config_makeconfig = self.gentooci.config.project['project']['config_makeconfig']
        for v in config_makeconfig:
            makeconf_list.append(v)
        # add ACCEPT_KEYWORDS from the project_data info
        keyword_data = yield self.gentooci.db.keywords.getKeywordById(project_data['keyword_id'])
        if project_data['status'] == 'unstable':
            makeconf_keyword = '~' + keyword_data['name']
        else:
            makeconf_keyword = keyword_data['name']
        makeconf_list.append('ACCEPT_KEYWORDS="' + makeconf_keyword + '"')
        makeconf_list.append('MAKEOPTS="-j14"')
        makeconf_string = separator1.join(makeconf_list)
        print(makeconf_string)
        yield self.build.addStepsAfterCurrentStep([
            steps.StringDownload(makeconf_string + separator1,
                                workerdest="make.conf",
                                workdir=portage_etc_path)
            ])
        # display the make.conf
        for line in makeconf_list:
            yield log.addStdout(line + '\n')
        return SUCCESS

class SetPackageDefault(BuildStep):

    name = 'SetPackageDefault'
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
        separator1 = '\n'
        separator2 = ' '
        log = yield self.addLog('package.*')
        self.aftersteps_list = []
        self.aftersteps_list.append(steps.MakeDirectory(dir='package.use',
                                workdir='/etc/portage/'))
        self.aftersteps_list.append(steps.MakeDirectory(dir='package.env',
                                workdir='/etc/portage/'))
        #FIXME: accept_keywords
        # add the needed package.* settings from db
        # add package use
        package_conf_use_list = []
        package_settings = yield self.gentooci.db.projects.getProjectPortagePackageByUuid(self.getProperty('project_data')['uuid'])
        for package_setting in package_settings:
            if package_setting['directory'] == 'use':
                package_conf_use_list.append(separator2.join(package_setting['package'],package_setting['value']))
        if self.getProperty('use_data') is not None:
            for k, v in self.getProperty('use_data').items():
                    for use, value in v.items():
                        if value:
                            package_conf_use_list.append(separator2.join([k, use]))
                        else:
                            package_conf_use_list.append(separator2.join([k, '-' + use]))
        if package_conf_use_list != []:
            package_conf_use_string = separator1.join(package_conf_use_list)
            self.aftersteps_list.append(
                        steps.StringDownload(package_conf_use_string + separator1,
                            workerdest='default.conf',
                            workdir='/etc/portage/package.use/'
                            )
                        )
            yield log.addStdout('File: ' + 'package.use/default.conf' + separator1)
            for line in package_conf_use_list:
                yield log.addStdout(line + separator1)
        # for test we need to add env and use
        #FIXME: check restrictions, test use mask and required use
        if self.getProperty('projectrepository_data')['test']:
            auxdb_iuses = yield self.gentooci.db.versions.getMetadataByUuidAndMatadata(self.getProperty("version_data")['uuid'], 'iuse')
            for auxdb_iuse in auxdb_iuses:
                iuse, status = getIUseValue(auxdb_iuse['value'])
                if iuse == 'test':
                    self.aftersteps_list.append(
                        steps.StringDownload(separator2.join(['=' + self.getProperty("cpv"),'test']) + separator1,
                            workerdest='test.conf',
                            workdir='/etc/portage/package.use/'
                            )
                        )
                    yield log.addStdout('File: ' + 'package.use/test.conf' + separator1)
                    yield log.addStdout(separator2.join(['=' + self.getProperty("cpv"),'test']) + separator1)
            self.aftersteps_list.append(
                        steps.StringDownload(separator2.join(['=' + self.getProperty("cpv"),'test.conf']) + separator1,
                            workerdest='test.conf',
                            workdir='/etc/portage/package.env/'
                            )
                        )
            yield log.addStdout('File: ' + 'package.env/test.conf' + separator1)
            yield log.addStdout(separator2.join(['=' + self.getProperty("cpv"),'test.conf']) + separator1)
        yield self.build.addStepsAfterCurrentStep(self.aftersteps_list)
        return SUCCESS

class SetEnvDefault(BuildStep):

    name = 'SetEnvDefault'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def getPortageEnv(self, portage_env_data, portage_env_dict = {}):
        for project_portage_env in portage_env_data:
            if not project_portage_env['name'] in portage_env_dict:
                portage_env_dict[project_portage_env['name']] = {
                    project_portage_env['makeconf_id'] : []
                    }
            if not project_portage_env['makeconf_id'] in portage_env_dict[project_portage_env['name']]:
                portage_env_dict[project_portage_env['name']][project_portage_env['makeconf_id']] = []
            portage_env_dict[project_portage_env['name']][project_portage_env['makeconf_id']].append(project_portage_env['value'])
        return portage_env_dict

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        project_data = self.getProperty('project_data')
        default_project_data = yield self.gentooci.db.projects.getProjectByName(self.gentooci.config.project['project']['update_db'])
        aftersteps_list = []
        separator1 = '\n'
        separator2 = ' '
        log = yield self.addLog('env')
        # create the dir
        aftersteps_list.append(steps.MakeDirectory(dir='env',
                                workdir='/etc/portage/'))
        #FIXME:
        # add env settings from the db
        default_project_portage_env_data = yield self.gentooci.db.projects.getProjectPortageEnvByUuid(default_project_data['uuid'])
        project_portage_env_data = yield self.gentooci.db.projects.getProjectPortageEnvByUuid(project_data['uuid'])
        project_portage_env_dict = yield self.getPortageEnv(default_project_portage_env_data, portage_env_dict = {})
        project_portage_env_dict = yield self.getPortageEnv(project_portage_env_data, portage_env_dict = project_portage_env_dict)
        print(project_portage_env_dict)
        for k, v in project_portage_env_dict.items():
            env_strings = []
            for a, b in v.items():
                variable_data = yield self.gentooci.db.portages.getVariableById(a)
                env_variable_string = variable_data['variable'] + '="' + separator2.join(b) + '"'
                env_strings.append(env_variable_string)
            yield self.build.addStepsAfterCurrentStep([
            steps.StringDownload(separator1.join(env_strings) + separator1,
                                workerdest=k + '.conf',
                                workdir='/etc/portage/env/')
            ])
            yield log.addStdout('File: ' + k + '.conf' + '\n')
            for line in env_strings:
                yield log.addStdout(line + '\n')
        yield self.build.addStepsAfterCurrentStep(aftersteps_list)
        return SUCCESS

class CheckPathLocal(BuildStep):

    name = 'CheckPathLocal'
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
        self.portage_path = yield os.path.join('etc', 'portage')
        self.profile_path = yield os.path.join(self.portage_path, 'make.profile')
        self.repos_path = yield os.path.join(self.portage_path, 'repos.conf')
        self.repository_basedir_db = yield os.path.join(self.master.basedir, 'repositorys')
        self.build_repository_basedir_db = yield os.path.join(self.getProperty("builddir"), 'repositorys')
        #print(self.repository_basedir_db)
        log = yield self.addLog('CheckPathLocal')
        #print(os.getcwd())
        print(self.getProperty("builddir"))
        #yield os.chdir(self.getProperty("builddir"))
        #print(os.getcwd())
        for x in [
                self.portage_path,
                self.profile_path,
                self.repos_path,
                ]:
            check_dir = yield os.path.join(self.getProperty("builddir"), x)
            if not Path(check_dir).is_dir():
                yield Path(check_dir).mkdir(parents=True)
                yield log.addStdout(' '.join(['Makeing missing dir', x]))
        if not Path(self.build_repository_basedir_db).is_dir():
            yield Path(self.build_repository_basedir_db).symlink_to(self.repository_basedir_db)
            yield log.addStdout(' '.join(['Makeing missing link', 'repositorys', 'to', self.repository_basedir_db]))
        return SUCCESS

class SetMakeProfileLocal(BuildStep):

    name = 'SetMakeProfileLocal'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        parent_path = yield os.path.join('etc','portage', 'make.profile', 'parent')
        if os.path.isfile(parent_path):
            return SKIPPED
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        self.profile_repository_data = yield self.gentooci.db.repositorys.getRepositoryByUuid(self.getProperty('project_data')['profile_repository_uuid'])
        self.repository_basedir = 'repositorys'
        makeprofiles_paths = []
        makeprofiles_data = yield self.gentooci.db.projects.getAllProjectPortageByUuidAndDirectory(self.getProperty('project_data')['uuid'], 'make.profile')
        for makeprofile in makeprofiles_data:
            makeprofile_path = yield os.path.join(self.repository_basedir, self.profile_repository_data['name'], 'profiles', makeprofile['value'], '')
            makeprofiles_paths.append('../../../' + makeprofile_path)
        yield WriteTextToFile(parent_path, makeprofiles_paths)
        return SUCCESS

class SetReposConfLocal(BuildStep):

    name = 'SetReposConfLocal'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        repos_conf_path = yield os.path.join('etc', 'portage', 'repos.conf')
        repos_conf_default_path = yield os.path.join(repos_conf_path, 'default.conf')
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        self.repository_basedir_db = yield os.path.join(self.master.basedir, 'repositorys')
        if not os.path.isfile(repos_conf_default_path):
            # setup the default.conf
            repos_conf_data = yield self.gentooci.db.projects.getProjectPortageByUuidAndDirectory(self.getProperty('project_data')['uuid'], 'repos.conf')
            if repos_conf_data is None:
                print('Default repo is not set in repos.conf')
                return FAILURE
            default_conf = []
            default_conf.append('[DEFAULT]')
            default_conf.append('main-repo = ' + repos_conf_data['value'])
            default_conf.append('auto-sync = no')
            yield WriteTextToFile(repos_conf_default_path, default_conf)
        repos_conf_repository_path = yield os.path.join(repos_conf_path, self.getProperty("repository_data")['name'] + '.conf')
        if not os.path.isfile(repos_conf_repository_path):
            repository_path = yield os.path.join(self.repository_basedir_db, self.getProperty("repository_data")['name'])
            repository_conf = []
            repository_conf.append('[' + self.getProperty("repository_data")['name'] + ']')
            repository_conf.append('location = ' + repository_path)
            repository_conf.append('sync-uri = ' + self.getProperty("repository_data")['url'])
            repository_conf.append('sync-type = git')
            repository_conf.append('auto-sync = no')
            yield WriteTextToFile(repos_conf_repository_path, repository_conf)
        return SUCCESS

class SetMakeConfLocal(BuildStep):

    name = 'SetMakeConfLocal'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        make_conf_path = yield os.path.join('etc', 'portage', 'make.conf')
        if os.path.isfile(make_conf_path):
            return SUCCESS
        makeconf_list = []
        makeconf_list.append('CFLAGS=""')
        makeconf_list.append('CXXFLAGS=""')
        makeconf_list.append('ACCEPT_LICENSE="*"')
        makeconf_list.append('USE=""')
        makeconf_list.append('ACCEPT_KEYWORDS="~riscv riscv"')
        makeconf_list.append('EMERGE_DEFAULT_OPTS=""')
        makeconf_list.append('ABI_X86="32 64"')
        makeconf_list.append('FEATURES="sandbox"')
        yield WriteTextToFile(make_conf_path, makeconf_list)
        return SUCCESS
