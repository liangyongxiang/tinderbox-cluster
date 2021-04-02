# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os
import io

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
from buildbot.plugins import steps

from buildbot_gentoo_ci.steps import master as master_steps

@defer.inlineCallbacks
def WriteTextToFile(path, text_list):
    separator = '\n'
    text_string = separator.join(text_list)
    with open(path, "a") as f:
        yield f.write(text_string)
        yield f.write(separator)
        yield f.close

def PersOutputOfEbuildSH(rc, stdout, stderr):
    metadata = None
    NoSplit = []
    NoSplit.append('DESCRIPTION')
    #make dict of the stout
    index = 1
    metadata_line_dict = {}
    for text_line in stdout.splitlines():
        metadata_line_dict[index] = text_line
        index = index + 1
    # should have 22 lines
    if len(auxdbkeys) != index -1:
        # number of lines is incorrect.
        return {
            'auxdb' : metadata
            }
    # split all keys to list instead of speces
    metadata = {}
    i = 1
    for key in auxdbkeys:
        if metadata_line_dict[i] == '':
            metadata[key] = None
        else:
            if ' ' in metadata_line_dict[i] and key not in NoSplit:
                metadata[key] = metadata_line_dict[i].split(' ')
            else:
                metadata[key] = []
                metadata[key].append(metadata_line_dict[i])
        i = i + 1
    return {
        'auxdb' : metadata
        }

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
        shell_commad_list.append(makeprofile_path)
        shell_commad_list.append('/etc/portage/make.profile')
        yield self.build.addStepsAfterCurrentStep([
            steps.ShellCommandNewStyle(
                        command=shell_commad_list,
                        workdir='/'
                )
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
                makeconf_variable_list.append('split-log')
                makeconf_variable_list.append('compress-build-logs')
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
                makeconf_variable_list.append('--quiet-build=y')
                makeconf_variable_list.append('--quiet-fail=y')
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
        makeconf_list.append('DISTDIR="/var/cache/portage/distfiles"')
        makeconf_list.append('PORTAGE_ELOG_CLASSES="*"')
        # We need echo:info to get the logfile name
        makeconf_list.append('PORTAGE_ELOG_SYSTEM="save:* echo:info"')
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
        project_data = self.getProperty('project_data')
        aftersteps_list = []
        packagedir_list = []
        packagedir_list.append('env')
        #FIXME:
        # get list what dir we need to make from db
        # create the dirs
        for packagedir in packagedir_list:
            aftersteps_list.append(steps.MakeDirectory(dir='package.' + packagedir,
                                workdir='/etc/portage/'))
        #FIXME:
        # add the needed package.* settings from db
        yield self.build.addStepsAfterCurrentStep(aftersteps_list)
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
        default_project_data = yield self.gentooci.db.projects.getProjectByName(self.gentooci.config.project['project'])
        aftersteps_list = []
        separator1 = '\n'
        separator2 = ' '
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
        yield self.build.addStepsAfterCurrentStep(aftersteps_list)
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
            return SUCCESS
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        self.repository_basedir = self.gentooci.config.project['repository_basedir']
        makeprofiles_paths = []
        makeprofiles_data = yield self.gentooci.db.projects.getAllProjectPortageByUuidAndDirectory(self.getProperty('project_data')['uuid'], 'make.profile')
        for makeprofile in makeprofiles_data:
            makeprofile_path = yield os.path.join(self.repository_basedir, self.getProperty("profile_repository_data")['name'], 'profiles', makeprofile['value'], '')
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
        # the path should be set in the confg
        self.repository_basedir2 = '/home/repos2/'
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
            repository_path = yield os.path.join(self.repository_basedir2, self.getProperty("repository_data")['name'])
            repository_conf = []
            repository_conf.append('[' + self.getProperty("repository_data")['name'] + ']')
            repository_conf.append('location = ' + repository_path)
            repository_conf.append('sync-uri = ' + self.getProperty("repository_data")['mirror_url'])
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
        makeconf_list.append('ACCEPT_KEYWORDS="~amd64 amd64"')
        makeconf_list.append('EMERGE_DEFAULT_OPTS=""')
        makeconf_list.append('ABI_X86="32 64"')
        makeconf_list.append('FEATURES="sandbox"')
        yield WriteTextToFile(make_conf_path, makeconf_list)
        return SUCCESS

class SetEnvForEbuildSH(BuildStep):

    name = 'SetEnvForEbuildSH'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def getEapiFromFile(self):
        with io.open(_unicode_encode(self.getProperty("ebuild_file"),
            encoding=_encodings['fs'], errors='strict'),
            mode='r', encoding=_encodings['repo.content'],
            errors='replace') as f:
            _eapi, _eapi_lineno = _parse_eapi_ebuild_head(f)

        return _eapi

    @defer.inlineCallbacks
    def run(self):
        addStepEbuildSH = []
        ebuild_commands = []
        ebuild_env = {}
        config_root = yield os.path.join(self.getProperty("builddir"), '')
        mysettings = yield portage_config(config_root = config_root)

        #Get EAPI from file and add it to env
        eapi = yield self.getEapiFromFile()
        print(eapi)
        if eapi is None or not eapi_is_supported(eapi):
            print('invalid eapi')
            eapi = '0'
        print(eapi_is_supported(eapi))
        ebuild_env['EAPI'] = eapi

        #FIXME: check manifest on ebuild_file

        #Setup ENV
        category = yield catpkgsplit(self.getProperty("cpv"))[0]
        package = yield catpkgsplit(self.getProperty("cpv"))[1]
        version = yield catpkgsplit(self.getProperty("cpv"))[2]
        revision = yield catpkgsplit(self.getProperty("cpv"))[3]
        portage_bin_path = mysettings["PORTAGE_BIN_PATH"]
        ebuild_sh_path = yield os.path.join(portage_bin_path, 'ebuild.sh')
        #ebuild_env['PORTAGE_DEBUG'] = '1'
        ebuild_env['EBUILD_PHASE'] = 'depend'
        ebuild_env['CATEGORY'] = category
        ebuild_env['P'] = package + '-' + version
        ebuild_env['PN'] = package
        ebuild_env['PR'] = revision
        ebuild_env['PV'] = version
        if revision == 'r0':
            ebuild_env['PF'] = ebuild_env['P']
            ebuild_env['PVR'] = version
        else:
            ebuild_env['PF'] = ebuild_env['P'] + '-' + revision
            ebuild_env['PVR'] = version + '-' + revision
        ebuild_env['PORTAGE_BIN_PATH'] = portage_bin_path
        ebuild_env['EBUILD'] = self.getProperty("ebuild_file")
        ebuild_env['PORTAGE_PIPE_FD'] = '1'
        ebuild_env['WORKDIR'] = yield os.path.join(mysettings["PORTAGE_TMPDIR"], 'portage', category, ebuild_env['PF'], 'work')
        ebuild_env['PORTAGE_ECLASS_LOCATIONS'] = self.getProperty("repository_path")

        #FIXME: use sandbox if in FEATURES
        ebuild_commands.append(ebuild_sh_path)
        ebuild_commands.append('depend')

        addStepEbuildSH.append(master_steps.MasterSetPropertyFromCommand(
                                                            name = 'RunEbuildSH',
                                                            haltOnFailure = True,
                                                            flunkOnFailure = True,
                                                            command=ebuild_commands,
                                                            env=ebuild_env,
                                                            workdir=self.getProperty("builddir"),
                                                            strip=False,
                                                            extract_fn=PersOutputOfEbuildSH
                                                            ))
        yield self.build.addStepsAfterCurrentStep(addStepEbuildSH)
        return SUCCESS

class GetAuxMetadata(BuildStep):

    name = 'GetAuxMetadata'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    #@defer.inlineCallbacks
    def thd_getAuxDbKeys(self):
        auxdbs = self.myportdb.aux_get(self.getProperty("cpv"), auxdbkeys, myrepo=self.getProperty("repository_data")['name'])
        return auxdbs

    @defer.inlineCallbacks
    def run(self):
        config_root = yield os.path.join(self.getProperty("builddir"), '')
        # setup mysettings and myportdb
        mysettings = yield portage_config(config_root = config_root)
        self.myportdb = yield portdbapi(mysettings=mysettings)
        auxdbs = yield self.thd_getAuxDbKeys()
        metadata = None
        NoSplit = []
        NoSplit.append('DESCRIPTION')
        # should have 22 lines
        if len(auxdbkeys) != len(auxdbs) or not isinstance(auxdbs, list):
            # number of lines is incorrect or not a list.
            print("Lines don't match or not a list")
            yield self.myportdb.close_caches()
            yield portdbapi.portdbapi_instances.remove(self.myportdb)
            #self.setProperty('auxdb', metadata, 'auxdb')
            return FAILURE
        # split all keys to list instead of speces
        metadata = {}
        i = 0
        for key in auxdbkeys:
            if auxdbs[i] == '':
                metadata[key] = None
            else:
                if ' ' in auxdbs[i] and key not in NoSplit:
                    metadata[key] = auxdbs[i].split(' ')
                else:
                    metadata[key] = []
                    metadata[key].append(auxdbs[i])
            i = i + 1
        self.setProperty('auxdb', metadata, 'auxdb')
        yield self.myportdb.close_caches()
        yield portdbapi.portdbapi_instances.remove(self.myportdb)
        return SUCCESS
