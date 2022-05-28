# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os
import re
import json

from portage.versions import catpkgsplit, cpv_getversion
from portage.dep import dep_getcpv, dep_getslot, dep_getrepo

from twisted.internet import defer
from twisted.python import log

from buildbot.process.buildstep import BuildStep
from buildbot.process.results import SUCCESS
from buildbot.process.results import FAILURE
from buildbot.process.results import SKIPPED
from buildbot.plugins import steps

#FIXME: should be set in config
hosturl = 'http://77.110.8.67:8000'

def PersOutputOfEmerge(rc, stdout, stderr):
    emerge_output = {}
    emerge_output['rc'] = rc
    emerge_output['preserved_libs'] = False
    emerge_output['change_use'] = False
    emerge_output['circular_deps'] = False
    emerge_output['failed'] = False
    package_dict = {}
    log_path_list = []
    print(stderr)
    # split the lines
    for line in stdout.split('\n'):
        # package dict
        subdict = {}
        if line.startswith('[ebuild') or line.startswith('[binary') or line.startswith('[nomerge'):
            # if binaries
            if line.startswith('[ebuild') or line.startswith('[nomerge'):
                subdict['binary'] = False
            else:
                subdict['binary'] = True
            # action [ N ] stuff
            subdict['action'] = line[8:15].replace(' ', '')
            # We my have more then one spece betvine ] and cpv
            pkg_line = re.sub(' +', ' ', line)
            # get pkg
            pkg = '=' + re.search('] (.+?) ', pkg_line).group(1)
            # repository
            subdict['repository'] = dep_getrepo(pkg)
            # slot
            subdict['slot'] = dep_getslot(pkg)
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
            # FIXME: CPU_FLAGS_X86 list
            package_dict[dep_getcpv(pkg)] = subdict
        if line.startswith('>>>'):
            if line.startswith('>>> Failed to'):
                emerge_output['failed'] = line.split(' ')[4][:-1]
            if line.endswith('.log.gz') and emerge_output['failed']:
                log_path_list.append(line.split(' ')[2])
            #FIXME: Handling of >>> output
            pass
        if line.startswith('!!!'):
            #FIXME: Handling of !!! output
            if line.startswith('!!! existing preserved libs'):
                pass
        if line.startswith(' * '):
            if line.endswith('.log.gz'):
                log_path_list.append(line.split(' ')[4])
        #FIXME: Handling of depclean output dict of packages that get removed or saved
    emerge_output['packages'] = package_dict

    # split the lines
    #FIXME: Handling of stderr output
    stderr_line_list = []
    for line in stderr.split('\n'):
        if 'Change USE:' in line:
            line_list = line.split(' ')
            change_use_list = []
            # get cpv
            cpv_split = line_list[1].split(':')
            change_use = {}
            # add use flags
            if line_list[4].startswith('+') or line_list[4].startswith('-'):
                # we only support tre for now
                if line_list[4].endswith(')'):
                    change_use_list.append(line_list[4].replace(')', ''))
                elif line_list[5].endswith(')'):
                    change_use_list.append(line_list[4])
                    change_use_list.append(line_list[5].replace(')', ''))
                elif line_list[6].endswith(')'):
                    change_use_list.append(line_list[4])
                    change_use_list.append(line_list[5])
                    change_use_list.append(line_list[6].replace(')', ''))
                elif not line_list[6].endswith(')'):
                    change_use_list.append(line_list[4])
                    change_use_list.append(line_list[5])
                    change_use_list.append(line_list[6])
                else:
                    change_use_list = False
            if change_use_list:
                change_use[cpv_split[0]] = change_use_list
                emerge_output['change_use'] = change_use
        err_line_list = []
        if line.startswith(' * '):
            if line.endswith('.log.gz'):
                log_path = line.split(' ')[3]
                if log_path not in inlog_path_list:
                    log_path_list.append(log_path)
            #FIXME: make dict of cpv listed in the circular dependencies
            if line.endswith('circular dependencies:'):
                emerge_output['circular_deps'] = True
            stderr_line_list.append(line)
    emerge_output['stderr'] = stderr_line_list
    emerge_output['log_paths'] = log_path_list

    return {
        'emerge_output' : emerge_output
        }

def PersOutputOfPkgCheck(rc, stdout, stderr):
    pkgcheck_output = {}
    pkgcheck_output['rc'] = rc
    print(stdout)
    pkgcheck_json_list = []
    # split the lines
    for line in stdout.split('\n'):
        if line.startswith('{"'):
            pkgcheck_json_list.append(json.loads(line))
    pkgcheck_output['pkgcheck_json'] = pkgcheck_json_list
    #FIXME: Handling of stderr output
    return {
        'pkgcheck_output' : pkgcheck_output
        }

def PersOutputOfDepclean(rc, stdout, stderr):
    depclean_output = {}
    depclean_output['rc'] = rc
    print(stderr)
    depclean_output['stderr'] = stderr
    package_list = False
    for line in stdout.split('\n'):
        if line.startswith('All selected packages:'):
            line_tmp = line.replace('All selected packages: ', '')
            package_list = line_tmp.split(' ')
    depclean_output['packages'] = package_list
    return {
        'depclean_output' : depclean_output
        }

def PersOutputOfEmergeInfo(rc, stdout, stderr):
    emerge_info_output = {}
    emerge_info_output['rc'] = rc
    emerge_info_list = []
    for line in stdout.split('\n'):
        emerge_info_list.append(line)
    emerge_info_output['emerge_info'] = emerge_info_list
    return {
        'emerge_info_output' : emerge_info_output
        }

def PersOutputOfElogLs(rc, stdout, stderr):
    elog_ls_output = {}
    elog_ls_output['rc'] = rc
    elog_ls_list = []
    for line in stdout.split('\n'):
        elog_ls_list.append(line)
    elog_ls_output['elog_ls'] = elog_ls_list
    return {
        'elog_ls_output' : elog_ls_output
        }

def PersOutputOfBuildWorkdir(rc, stdout, stderr):
    build_workdir_find_output = {}
    build_workdir_find_output['rc'] = rc
    build_workdir_find_list = []
    for line in stdout.split('\n'):
        find_line = line.replace('./', '')
        if find_line != '':
            build_workdir_find_list.append(find_line)
    build_workdir_find_output['build_workdir_find'] = build_workdir_find_list
    return {
        'build_workdir_find_output' : build_workdir_find_output
        }

class TriggerRunBuildRequest(BuildStep):
    
    name = 'TriggerRunBuildRequest'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, projectrepository_data, use_data, project_data, **kwargs):
        self.projectrepository_data = projectrepository_data
        self.use_data = use_data
        self.project_data = project_data
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        if self.getProperty('project_build_data') is None:
            project_build_data = {}
            project_build_data['project_uuid'] = self.project_data['uuid']
            project_build_data['version_uuid'] = self.getProperty("version_data")['uuid']
            project_build_data['status'] = 'waiting'
            project_build_data['requested'] = False
            project_build_data['id'], project_build_data['build_id'] = yield self.gentooci.db.builds.addBuild(
                                                                                            project_build_data)
        else:
            project_build_data = self.getProperty('project_build_data')
        yield self.build.addStepsAfterCurrentStep([
                steps.Trigger(
                    schedulerNames=['run_build_request'],
                        waitForFinish=False,
                        updateSourceStamp=False,
                        set_properties={
                            'cpv' : self.getProperty("cpv"),
                            'version_data' : self.getProperty("version_data"),
                            'projectrepository_data' : self.projectrepository_data,
                            'use_data' : self.use_data,
                            'fullcheck' : self.getProperty("fullcheck"),
                            'project_build_data' : project_build_data,
                            'project_uuid' : self.project_data['uuid']
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
            print(projectrepository_data)
            # get project data
            project_data = yield self.gentooci.db.projects.getProjectByUuid(projectrepository_data['project_uuid'])
            #FIXME: check if we have working workers
            project_workers = yield self.gentooci.db.projects.getWorkersByProjectUuid(project_data['uuid'])
            if project_workers == []:
                print('No Workers on this profile')
                continue
            # check if auto, enabled and not in config.project['project']
            if project_data['auto'] is True and project_data['enabled'] is True and project_data['name'] != self.gentooci.config.project['project']['update_db']:
                # set Property projectrepository_data so we can use it in the trigger
                # get name o project keyword
                project_keyword_data = yield self.gentooci.db.keywords.getKeywordById(project_data['keyword_id'])
                # if not * (all keywords)
                if project_keyword_data['name'] != '*' or project_data['status'] == 'all':
                    self.setProperty('fullcheck', False, 'fullcheck')
                    # get status of the keyword on cpv
                    if self.getProperty("version_keyword_dict") is not None:
                        if project_keyword_data['name'] in self.getProperty("version_keyword_dict"):
                            version_keywords_data = self.getProperty("version_keyword_dict")[project_keyword_data['name']]
                            # if match trigger BuildRequest on cpv
                            if project_data['status'] == version_keywords_data['status']:
                                yield self.build.addStepsAfterCurrentStep([TriggerRunBuildRequest(
                                    projectrepository_data = projectrepository_data,
                                    use_data = None,
                                    project_data = project_data
                                )])
        return SUCCESS

class SetupPropertys(BuildStep):
    name = 'Setup propertys for building'
    description = 'Running'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        # set this in config
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        print('build this %s' % self.getProperty("cpv"))
        self.setProperty('portage_repos_path', self.gentooci.config.project['project']['worker_portage_repos_path'], 'portage_repos_path')
        projectrepository_data = self.getProperty('projectrepository_data')
        print(projectrepository_data)
        project_data = yield self.gentooci.db.projects.getProjectByUuid(projectrepository_data['project_uuid'])
        repository_data = yield self.gentooci.db.repositorys.getRepositoryByUuid(projectrepository_data['repository_uuid'])
        self.setProperty('project_data', project_data, 'project_data')
        self.setProperty('repository_data', repository_data, 'repository_data')
        self.setProperty('preserved_libs', False, 'preserved-libs')
        self.setProperty('depclean', False, 'depclean')
        self.setProperty('cpv_build', False, 'cpv_build')
        self.setProperty('pkg_check_log_data', None, 'pkg_check_log_data')
        self.setProperty('faild_version_data', None, 'faild_version_data')
        self.setProperty('rerun', 0, 'rerun')
        project_build_data = self.getProperty('project_build_data')
        project_build_data['status'] = 'in-progress'
        project_build_data['buildbot_build_id'] = self.getProperty("buildnumber")
        yield self.gentooci.db.builds.setSatusBuilds(
                                                    project_build_data['id'],
                                                    project_build_data['status'])
        yield self.gentooci.db.builds.setBuildbotBuildIdBuilds(
                                                    project_build_data['id'],
                                                    project_build_data['buildbot_build_id'])
        self.setProperty('project_build_data', project_build_data, 'project_build_data')
        print(self.getProperty("project_build_data"))
        self.masterdest = yield os.path.join(self.master.basedir, 'workers', self.getProperty('workername'), str(self.getProperty("buildnumber")))
        self.setProperty('masterdest', self.masterdest, 'masterdest')
        self.descriptionDone = ' '.join([self.getProperty("cpv"), 'for project', self.getProperty('project_data')['name']])
        return SUCCESS

class UpdateRepos(BuildStep):

    name = 'UpdateRepos'
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
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        portage_repos_path = self.getProperty('portage_repos_path')
        project_data = self.getProperty('project_data')
        # update/add all repos that in project_repository for the project
        projects_repositorys_data = yield self.gentooci.db.projects.getRepositorysByProjectUuid(project_data['uuid'])
        for project_repository_data in projects_repositorys_data:
            repository_data = yield self.gentooci.db.repositorys.getRepositoryByUuid(project_repository_data['repository_uuid'])
            if self.rootworkdir:
                repository_path = os.path.join(self.rootworkdir, portage_repos_path[1:], repository_data['name'])
            else:
                repository_path = os.path.join(portage_repos_path, repository_data['name'], '')
            yield self.build.addStepsAfterCurrentStep([
                steps.Git(repourl=repository_data['url'],
                            name = 'Git pull ' +  repository_data['name'],
                            mode='full',
                            submodules=True,
                            alwaysUseLatest=True,
                            workdir=repository_path)
            ])
        return SUCCESS

class RunEmerge(BuildStep):

    description = 'Running'
    descriptionDone = 'Ran'
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, step=None, **kwargs):
        self.step = step
        super().__init__(**kwargs)
        self.descriptionSuffix = self.step
        self.name = 'Setup emerge for ' + self.step + ' step'
        self.build_env = {}
        #FIXME: Set build timeout in config
        self.build_timeout = 1800

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        project_data = self.getProperty('project_data')
        projects_emerge_options = yield self.gentooci.db.projects.getProjectEmergeOptionsByUuid(project_data['uuid'])
        self.stepname = 'Run emerge ' + 'step ' + self.step
        shell_commad_list = [
                    'emerge',
                    '-v'
                    ]
        aftersteps_list = []
        # set env
        # https://bugs.gentoo.org/683118
        # export TERM=linux
        # export TERMINFO=/etc/terminfo
        self.build_env['TERM'] = 'linux'
        self.build_env['TERMINFO'] = '/etc/terminfo'
        # Lang
        self.build_env['LANG'] = 'C.utf8'
        self.build_env['LC_MESSAGES'] = 'C'
        # no color
        self.build_env['CARGO_TERM_COLOR'] = 'never'
        self.build_env['GCC_COLORS'] = '0'
        self.build_env['OCAML_COLOR'] = 'never'
        self.build_env['PY_FORCE_COLOR'] = '0'
        self.build_env['PYTEST_ADDOPTS'] = '--color=no'
        self.build_env['NO_COLOR'] = '1'
        # not all terms support urls
        self.build_env['GCC_URLS'] = 'no'
        self.build_env['TERM_URLS'] = 'no'

        if self.step == 'pre-update':
            shell_commad_list.append('-uDN')
            shell_commad_list.append('--changed-deps')
            shell_commad_list.append('--changed-use')
            shell_commad_list.append('--pretend')
            shell_commad_list.append('@world')
            # don't build bin for virtual and acct-*
            shell_commad_list.append('--buildpkg-exclude')
            shell_commad_list.append('virtual')
            shell_commad_list.append('--buildpkg-exclude')
            shell_commad_list.append('acct-*')
            aftersteps_list.append(
                steps.SetPropertyFromCommand(
                        name = self.stepname,
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
            # don't build bin for virtual and acct-*
            shell_commad_list.append('--buildpkg-exclude')
            shell_commad_list.append('virtual')
            shell_commad_list.append('--buildpkg-exclude')
            shell_commad_list.append('acct-*')
            aftersteps_list.append(
                steps.SetPropertyFromCommand(
                        name = self.stepname,
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=PersOutputOfEmerge,
                        workdir='/',
                        timeout=self.build_timeout
                ))
            aftersteps_list.append(CheckEmergeLogs('update'))
            if projects_emerge_options['preserved_libs']:
                self.setProperty('preserved_libs', True, 'preserved-libs')

        if self.step == 'preserved-libs' and self.getProperty('preserved_libs'):
            shell_commad_list.append('-q')
            shell_commad_list.append('@preserved-rebuild')
            aftersteps_list.append(
                steps.SetPropertyFromCommand(
                        name = self.stepname,
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=PersOutputOfEmerge,
                        workdir='/',
                        timeout=self.build_timeout
                ))
            aftersteps_list.append(CheckEmergeLogs('preserved-libs'))
            self.setProperty('preserved_libs', False, 'preserved-libs')

        if self.step == 'pre-depclean' and projects_emerge_options['depclean']:
            shell_commad_list.append('--pretend')
            shell_commad_list.append('--depclean')
            aftersteps_list.append(
                steps.SetPropertyFromCommand(
                        name = self.stepname,
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=PersOutputOfDepclean,
                        workdir='/'
                ))
            aftersteps_list.append(CheckDepcleanLogs('pre-depclean'))
            self.setProperty('depclean', False, 'depclean')

        if self.step == 'depclean' and projects_emerge_options['depclean']:
            shell_commad_list.append('-q')
            shell_commad_list.append('--depclean')
            # add exlude cpv if needed
            if self.getProperty('depclean'):
                pass
            aftersteps_list.append(
                steps.SetPropertyFromCommand(
                        name = self.stepname,
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=PersOutputOfDepclean,
                        workdir='/'
                ))
            aftersteps_list.append(CheckDepcleanLogs('depclean'))

        if self.step == 'match':
            packages_excludes = yield self.gentooci.db.projects.getProjectPortagePackageByUuidAndExclude(self.getProperty('project_data')['uuid'])
            cpv = self.getProperty("cpv")
            c = yield catpkgsplit(cpv)[0]
            p = yield catpkgsplit(cpv)[1]
            # Check if package is on the exclude list
            if packages_excludes != []:
                print(packages_excludes)
                print(cpv)
                for package_exclude in packages_excludes:
                    if '/' in package_exclude['package']:
                        if package_exclude['package'] == c + '/' + p:
                            return SKIPPED
                    else:
                        if package_exclude['package'] == p:
                            return SKIPPED
            shell_commad_list.append('-pO')
            # don't use bin for match
            shell_commad_list.append('--usepkg=n')
            shell_commad_list.append(c + '/' + p)
            aftersteps_list.append(
                steps.SetPropertyFromCommand(
                        name = self.stepname,
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=PersOutputOfEmerge,
                        workdir='/',
                        timeout=self.build_timeout
                ))
            aftersteps_list.append(CheckEmergeLogs('match'))

        if self.step == 'pre-build':
            cpv = self.getProperty("cpv")
            c = yield catpkgsplit(cpv)[0]
            p = yield catpkgsplit(cpv)[1]
            shell_commad_list.append('=' + self.getProperty('cpv'))
            # we don't use the bin for the requsted cpv
            shell_commad_list.append('--usepkg-exclude')
            shell_commad_list.append(c + '/' + p)
            # don't build bin for virtual and acct-*
            shell_commad_list.append('--buildpkg-exclude')
            shell_commad_list.append('virtual')
            shell_commad_list.append('--buildpkg-exclude')
            shell_commad_list.append('acct-*')
            shell_commad_list.append('-p')
            aftersteps_list.append(
                steps.SetPropertyFromCommand(
                        warnOnWarnings = True,
                        warnOnFailure = True,
                        flunkOnFailure = False,
                        flunkOnWarnings = False,
                        name = self.stepname,
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=PersOutputOfEmerge,
                        workdir='/',
                        timeout=self.build_timeout
                ))
            aftersteps_list.append(CheckEmergeLogs('pre-build'))

        if self.step == 'build':
            cpv = self.getProperty("cpv")
            c = yield catpkgsplit(cpv)[0]
            p = yield catpkgsplit(cpv)[1]
            if projects_emerge_options['oneshot']:
                shell_commad_list.append('-1')
            shell_commad_list.append('=' + self.getProperty('cpv'))
            # we don't use the bin for the requsted cpv
            shell_commad_list.append('--usepkg-exclude')
            shell_commad_list.append(c + '/' + p)
            # don't build bin for virtual and acct-*
            shell_commad_list.append('--buildpkg-exclude')
            shell_commad_list.append('virtual')
            shell_commad_list.append('--buildpkg-exclude')
            shell_commad_list.append('acct-*')
            aftersteps_list.append(
                steps.SetPropertyFromCommand(
                        name = self.stepname,
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=PersOutputOfEmerge,
                        workdir='/',
                        env=self.build_env,
                        timeout=self.build_timeout
                ))
            aftersteps_list.append(CheckEmergeLogs('build'))
            if projects_emerge_options['preserved_libs']:
                self.setProperty('preserved_libs', True, 'preserved-libs')

        if not self.step is None and aftersteps_list != []:
            yield self.build.addStepsAfterCurrentStep(aftersteps_list)
        return SUCCESS

class CheckElogLogs(BuildStep):

    name = 'Check elog logs'
    description = 'Running'
    descriptionDone = 'Ran'
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.aftersteps_list = []

    def addFileUploade(self, sourcefile, destfile, name, url, urlText):
        self.aftersteps_list.append(steps.FileUpload(
            name = name,
            mode = 0o644,
            workersrc = sourcefile,
            masterdest = destfile,
            url = url,
            urlText = urlText
        ))

    @defer.inlineCallbacks
    def run(self):
        elog_ls_output = self.getProperty('elog_ls_output')
        workdir = yield os.path.join('/', 'var', 'cache', 'portage', 'logs', 'elog')
        for elogfile in elog_ls_output['elog_ls']:
            if self.getProperty('faild_cpv'):
                cpv = self.getProperty('faild_cpv')
            else:
                cpv = self.getProperty('cpv')
            if elogfile.replace(':', '/').startswith(cpv):
                print(elogfile)
                destfile = yield os.path.join(self.getProperty('masterdest'), elogfile.replace('.log', '.elog'))
                sourcefile = yield os.path.join(workdir, elogfile)
                name = 'Upload Elogs'
                url = '/'.join([hosturl, self.getProperty('workername'), str(self.getProperty("buildnumber")), elogfile.replace('.log', '.elog')])
                urlText = elogfile
                self.addFileUploade(sourcefile, destfile, name, url, urlText)
        if self.aftersteps_list != []:
            yield self.build.addStepsAfterCurrentStep(self.aftersteps_list)
        return SUCCESS

class CheckBuildWorkDirs(BuildStep):

    name = 'Setup tar for taring the logs'
    description = 'Running'
    descriptionDone = 'Ran'
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.aftersteps_list = []

    @defer.inlineCallbacks
    def run(self):
        cpv = self.getProperty('faild_cpv')
        cpv_build_dir = yield os.path.join('/', 'var', 'tmp', 'portage', self.getProperty('cpv_build_dir'))
        compressed_log_file = cpv.replace('/', '_') + '.' + str(self.getProperty("buildnumber")) + '.logs.tar.bz2'
        masterdest_file = yield os.path.join(self.getProperty('masterdest'), compressed_log_file)
        # cpv_build_work_dir = yield os.path.join(cpv_build_dir, 'work')
        if self.getProperty('build_workdir_find_output')['build_workdir_find'] != []:
            shell_commad_list = []
            shell_commad_list.append('tar')
            shell_commad_list.append('-cjpf')
            shell_commad_list.append(compressed_log_file)
            for find_line in sorted(self.getProperty('build_workdir_find_output')['build_workdir_find']):
                print(find_line)
                filename = yield os.path.join('work', find_line)
                shell_commad_list.append(filename)
            self.aftersteps_list.append(
                steps.ShellCommand(
                        name = 'Tar logs',
                        command = shell_commad_list,
                        workdir = cpv_build_dir
            ))
            self.aftersteps_list.append(steps.FileUpload(
                name = 'Upload find logs',
                mode = 0o644,
                workersrc = compressed_log_file,
                masterdest = masterdest_file,
                workdir = cpv_build_dir,
                url = '/'.join([hosturl, self.getProperty('workername'), str(self.getProperty("buildnumber")), compressed_log_file]),
                urlText = 'Compresed file for all finds'
            ))
        if self.aftersteps_list != []:
            yield self.build.addStepsAfterCurrentStep(self.aftersteps_list)
        return SUCCESS

class CheckEmergeLogs(BuildStep):

    description = 'Running'
    descriptionDone = 'Ran'
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, step=None,**kwargs):
        self.step = step
        super().__init__(**kwargs)
        self.descriptionSuffix = self.step
        self.name = 'Check emerge logs for ' + self.step + ' step'
        self.aftersteps_list = []
        self.log_data = {}
        self.faild_cpv = False

    @defer.inlineCallbacks
    def getVersionData(self, cpv):
        c = yield catpkgsplit(cpv)[0]
        p = yield catpkgsplit(cpv)[1]
        category_data = yield self.gentooci.db.categorys.getCategoryByName(c)
        package_data = yield self.gentooci.db.packages.getPackageByName(p,
                                                                        category_data['uuid'],
                                                                        self.getProperty('repository_data')['uuid'])
        if package_data is None:
            return None
        version = yield cpv_getversion(cpv)
        version_data = yield self.gentooci.db.versions.getVersionByName(version, package_data['uuid'])
        return version_data

    @defer.inlineCallbacks
    def createDistDir(self):
        workdir = yield os.path.join(self.master.basedir, 'workers', self.getProperty('workername'))
        self.aftersteps_list.append(steps.MasterShellCommand(
            name = 'Make directory for Uploaded files',
            command = ['mkdir', str(self.getProperty("buildnumber"))],
            workdir = workdir
        ))

    def addFileUploade(self, sourcefile, destfile, name, url, urlText):
        self.aftersteps_list.append(steps.FileUpload(
            name = name,
            mode = 0o644,
            workersrc = sourcefile,
            masterdest = destfile,
            url=url,
            urlText=urlText
        ))

    @defer.inlineCallbacks
    def getLogFile(self, cpv, log_dict):
        file = log_dict[cpv]['full_logname']
        destfile = yield os.path.join(self.getProperty('masterdest'), file)
        sourcefile = log_dict[cpv]['log_path']
        name = 'Upload build log'
        url = '/'.join([hosturl, self.getProperty('workername'), str(self.getProperty("buildnumber")), file])
        urlText = file
        self.addFileUploade(sourcefile, destfile, name, url, urlText)

    @defer.inlineCallbacks
    def getElogFiles(self, cpv):
        workdir = yield os.path.join('/', 'var', 'cache', 'portage', 'logs', 'elog')
        elog_cpv = cpv.replace('/', ':')
        shell_commad_list = []
        shell_commad_list.append('ls')
        #shell_commad_list.append(elog_cpv + '*')
        self.aftersteps_list.append(
                steps.SetPropertyFromCommand(
                        name = 'List elogs',
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=PersOutputOfElogLs,
                        workdir=workdir,
                        timeout=None
                ))
        self.aftersteps_list.append(CheckElogLogs())

    @defer.inlineCallbacks
    def getEmergeFiles(self, cpv):
        # get emerge info
        file = 'emerge_info.txt'
        destfile = yield os.path.join(self.getProperty('masterdest'), file)
        sourcefile = yield os.path.join('/', 'tmp', file)
        name = 'Upload emerge info'
        url = '/'.join([hosturl, self.getProperty('workername'), str(self.getProperty("buildnumber")), file])
        urlText = 'emerge --info and package info'
        self.addFileUploade(sourcefile, destfile, name, url, urlText)
        # get emerge.log
        file = 'emerge.log'
        destfile = yield os.path.join(self.getProperty('masterdest'), file)
        sourcefile = yield os.path.join('/', 'var', 'log', file)
        name = 'Upload emerge log'
        url = '/'.join([hosturl, self.getProperty('workername'), str(self.getProperty("buildnumber")), file])
        urlText = 'emerge.log'
        self.addFileUploade(sourcefile, destfile, name, url, urlText)
        # world file
        file = 'world'
        destfile = yield os.path.join(self.getProperty('masterdest'), file)
        sourcefile = yield os.path.join('/', 'var', 'lib', 'portage', file)
        name = 'Upload world file'
        url = '/'.join([hosturl, self.getProperty('workername'), str(self.getProperty("buildnumber")), file])
        urlText = 'world file'
        self.addFileUploade(sourcefile, destfile, name, url, urlText)
        # get elogs
        self.getElogFiles(cpv)

    @defer.inlineCallbacks
    def getBuildWorkDirs(self, cpv):
        #FIXME:
        # get files from the build workdir
        cpv_build_dir = yield os.path.join('/', 'var', 'tmp', 'portage', cpv)
        print(cpv_build_dir)
        self.setProperty('cpv_build_dir', cpv_build_dir, 'cpv_build_dir')
        cpv_build_work_dir = yield os.path.join(cpv_build_dir, 'work')
        #FIXME: take find pattern from db
        find_pattern_list = ['meson-log.txt', 'CMakeCache.txt', 'testlog.txt', '*.out', 'project-config.jam', 'testlog-x11.txt']
        shell_commad_list = []
        # we have *.log as default
        shell_commad_list.append('find')
        shell_commad_list.append('-name')
        shell_commad_list.append('*.log')
        for find_pattern in find_pattern_list:
            shell_commad_list.append('-o')
            shell_commad_list.append('-name')
            shell_commad_list.append(find_pattern)
        self.aftersteps_list.append(
                steps.SetPropertyFromCommand(
                        name = 'Find logs',
                        command = shell_commad_list,
                        strip = True,
                        extract_fn = PersOutputOfBuildWorkdir,
                        workdir = cpv_build_work_dir
                ))
        self.aftersteps_list.append(CheckBuildWorkDirs())

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        project_data = self.getProperty('project_data')
        projects_emerge_options = yield self.gentooci.db.projects.getProjectEmergeOptionsByUuid(project_data['uuid'])
        shell_commad_list = [
                    'emerge',
                    '-v'
                    ]
        emerge_output = self.getProperty('emerge_output')
        self.faild_cpv = emerge_output['failed']
        package_dict = emerge_output['packages']

        #FIXME: Prosees the logs and do stuff
        # preserved-libs
        if emerge_output['preserved_libs'] and projects_emerge_options['preserved_libs']:
            self.setProperty('preserved_libs', True, 'preserved-libs')

        # FIXME: check if cpv match
        if self.step == 'match'and self.getProperty('projectrepository_data')['build']:
            if self.getProperty('cpv') in package_dict:
                self.setProperty('cpv_build', True, 'cpv_build')
            print(self.getProperty('cpv_build'))

        #FIXME:
        # update package.* if needed and rerun pre-build max 3 times
        if self.step == 'pre-build':
            print(emerge_output)
            # this should be set in the config
            if self.getProperty('rerun') <= 3:
                # when we need to change use. we could rerun pre-build with
                # --autounmask-use=y --autounmask-write=y --autounmask-only=y
                # but we use --binpkg--respect-use=y in EMERGE_DEFAULT_OPTS
                # read man emerge for more
                if emerge_output['change_use']:
                    # add a zz file for autounmask use
                    separator = '\n'
                    separator2 = ' '
                    change_use_list = []
                    log = yield self.addLog('change_use')
                    for cpv, v in emerge_output['change_use'].items():
                        c = yield catpkgsplit(cpv)[0]
                        p = yield catpkgsplit(cpv)[1]
                        change_use_list.append(c + '/' + p)
                        for use_flag in v:
                            if use_flag.startswith('+'):
                                change_use_list.append(use_flag.replace('+', ''))
                            else:
                                change_use_list.append(use_flag)
                    change_use_string = separator2.join(change_use_list)
                    self.aftersteps_list.append(
                        steps.StringDownload(change_use_string + separator,
                            name = 'Update package.use flags',
                            workerdest='zz_autouse' + str(self.getProperty('rerun')),
                            workdir='/etc/portage/package.use/'
                            )
                        )
                    yield log.addStdout('File: ' + 'zz_autouse' + str(self.getProperty('rerun')) + '\n')
                    yield log.addStdout(change_use_string + '\n')
                    # rerun
                    self.aftersteps_list.append(RunEmerge(step='pre-build'))
                    self.setProperty('rerun', self.getProperty('rerun') + 1, 'rerun')

                # * Error: circular dependencies:
                if emerge_output['circular_deps'] is True:
                    circular_dep = None
                    print('circular_deps')
                    for cpv, v in package_dict.items():
                        print(cpv)
                        print(catpkgsplit(cpv))
                        p = yield catpkgsplit(cpv)[1]
                        if p == 'harfbuzz':
                            circular_dep = 'harfbuzz'
                    # media-libs/harfbuzz
                    # https://wiki.gentoo.org/wiki/User:Sam/Portage_help/Circular_dependencies#Solution
                    if circular_dep == 'harfbuzz':
                        shell_commad_list = []
                        shell_commad_list.append('emerge')
                        shell_commad_list.append('-v')
                        # FIXME: cpv my get deleted in the tree
                        cpv = 'x11-libs/pango-1.48.5-r1'
                        c = yield catpkgsplit(cpv)[0]
                        p = yield catpkgsplit(cpv)[1]
                        shell_commad_list.append('-1')
                        shell_commad_list.append('=' + cpv)
                        # we don't use the bin for the requsted cpv
                        shell_commad_list.append('--usepkg-exclude')
                        shell_commad_list.append(c + '/' + p)
                        # rebuild this
                        shell_commad_list.append('--buildpkg-exclude')
                        shell_commad_list.append('freetype')
                        shell_commad_list.append('--buildpkg-exclude')
                        shell_commad_list.append('harfbuzz')
                        # don't build bin for virtual and acct-*
                        shell_commad_list.append('--buildpkg-exclude')
                        shell_commad_list.append('virtual')
                        shell_commad_list.append('--buildpkg-exclude')
                        shell_commad_list.append('acct-*')
                        self.aftersteps_list.append(
                            steps.SetPropertyFromCommand(
                                command=shell_commad_list,
                                strip=True,
                                extract_fn=PersOutputOfEmerge,
                                workdir='/',
                                env={'USE': "-harfbuzz"},
                                timeout=None
                        ))
                        self.aftersteps_list.append(CheckEmergeLogs('extra-build'))
            else:
                # trigger parse_build_log with info about pre-build and it fail
                pass
        # Make Logfile dict
        if self.step == 'extra-build' or self.step == 'build':
            print(emerge_output)
            log_dict = {}
            # get cpv, logname and log path
            for log_path in emerge_output['log_paths']:
                c = log_path.split('/')[6]
                full_logname = log_path.split('/')[7]
                print(full_logname)
                pv = full_logname.split(':')[0]
                cpv = c + '/' + pv
                log_dict[cpv] = dict(
                                log_path = log_path,
                                full_logname = full_logname
                                )
            print(log_dict)
        if self.step == 'extra-build':
            #FIXME: Check if extra build did work
            self.aftersteps_list.append(RunEmerge(step='pre-build'))
            self.setProperty('rerun', self.getProperty('rerun') + 1, 'rerun')

        #FIXME:
        # Look for FAILURE and logname and download needed logfile and
        # trigger a logparser
        # local_log_path dir set in config
        # format /var/cache/portage/logs/build/gui-libs/egl-wayland-1.1.6:20210321-173525.log.gz
        if self.step == 'build':
            # Find log for cpv that was requested or did failed
            if not log_dict == {}:
                # requested cpv
                cpv = self.getProperty('cpv')
                faild_version_data = False
                if cpv in log_dict or self.faild_cpv in log_dict:
                    yield self.createDistDir()
                    if cpv in log_dict:
                        self.log_data[cpv] = log_dict[cpv]
                        yield self.getLogFile(cpv, log_dict)
                    if self.faild_cpv:
                        # failed and build requested cpv
                        if cpv == self.faild_cpv:
                            faild_version_data = self.getProperty("version_data")
                        else:
                            # failed but not build requested cpv
                            self.log_data[self.faild_cpv] = log_dict[self.faild_cpv]
                            yield self.getLogFile(self.faild_cpv, log_dict)
                            faild_version_data = yield self.getVersionData(self.faild_cpv)
                        self.setProperty('faild_cpv', self.faild_cpv, 'faild_cpv')
                        self.getEmergeFiles(self.faild_cpv)
                        self.getBuildWorkDirs(self.faild_cpv)
                    else:
                        self.getEmergeFiles(cpv)
                    self.aftersteps_list.append(steps.Trigger(
                        name = 'Setup properties for log parser and trigger it',
                        schedulerNames=['parse_build_log'],
                        waitForFinish=False,
                        updateSourceStamp=False,
                        set_properties={
                            'cpv' : self.getProperty("cpv"),
                            'faild_version_data' : faild_version_data,
                            'project_build_data' : self.getProperty('project_build_data'),
                            'log_build_data' : self.log_data,
                            'pkg_check_log_data' : self.getProperty("pkg_check_log_data"),
                            'repository_data' : self.getProperty('repository_data'),
                            'faild_cpv' : self.faild_cpv,
                            'step' : self.step,
                            'build_workername' : self.getProperty('workername')
                        }
                    ))
        if not self.step is None and self.aftersteps_list != []:
            yield self.build.addStepsAfterCurrentStep(self.aftersteps_list)
        return SUCCESS

class CheckDepcleanLogs(BuildStep):

    name = 'CheckDepcleanLogs'
    description = 'Running'
    descriptionDone = 'Ran'
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, step=None,**kwargs):
        self.step = step
        super().__init__(**kwargs)
        self.descriptionSuffix = self.step
        self.name = 'Check dep clean logs for ' + self.step + ' step'

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        project_data = self.getProperty('project_data')
        projects_emerge_options = yield self.gentooci.db.projects.getProjectEmergeOptionsByUuid(project_data['uuid'])
        depclean_output = self.getProperty('depclean_output')
        aftersteps_list = []
        # run depclean if needed
        if self.step == 'pre-depclean' and projects_emerge_options['depclean']:
            # FIXME: check if we don't remove needed stuff.
            # add it to Property depclean if needed
            if depclean_output['packages']:
                for cpv_tmp in depclean_output['packages']:
                    cpv = cpv_tmp.replace('=', '')
                self.setProperty('depclean', False, 'depclean')
                aftersteps_list.append(RunEmerge(step='depclean'))

        if not self.step is None and aftersteps_list != []:
            yield self.build.addStepsAfterCurrentStep(aftersteps_list)
        return SUCCESS

class RunPkgCheck(BuildStep):

    name = 'Setup PkgCheck step'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        projectrepository_data = self.getProperty('projectrepository_data')
        if not projectrepository_data['pkgcheck']:
            return SUCCESS
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        project_data = self.getProperty('project_data')
        portage_repos_path = self.getProperty('portage_repos_path')
        repository_path = yield os.path.join(portage_repos_path, self.getProperty('repository_data')['name'])
        cpv = self.getProperty("cpv")
        c = yield catpkgsplit(cpv)[0]
        p = yield catpkgsplit(cpv)[1]
        shell_commad_list = [
                    'pkgcheck',
                    'scan',
                    '-v'
                    ]
        shell_commad_list.append('-R')
        shell_commad_list.append('JsonReporter')
        aftersteps_list = []
        if projectrepository_data['pkgcheck'] == 'full':
            pkgcheck_workdir = yield os.path.join(repository_path, '')
        else:
            pkgcheck_workdir = yield os.path.join(repository_path, c, p, '')
        aftersteps_list.append(
            steps.SetPropertyFromCommand(
                        name='Run pkgcheck step',
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=PersOutputOfPkgCheck,
                        workdir=pkgcheck_workdir
            ))
        aftersteps_list.append(CheckPkgCheckLogs())
        yield self.build.addStepsAfterCurrentStep(aftersteps_list)
        return SUCCESS

class CheckPkgCheckLogs(BuildStep):

    name = 'Check pkgcheck logs'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        #self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        #project_data = self.getProperty('project_data')
        pkgcheck_output = self.getProperty('pkgcheck_output')
        print(pkgcheck_output)
        if pkgcheck_output['pkgcheck_json'] == []:
            return SKIPPED
        pkg_check_log_data = []
        c = yield catpkgsplit(self.getProperty("cpv"))[0]
        p = yield catpkgsplit(self.getProperty("cpv"))[1]
        v = yield cpv_getversion(self.getProperty("cpv"))
        for json_dict in pkgcheck_output['pkgcheck_json']:
            for k, i in json_dict[c][p].items():
                if k == v or k == '_info' or k == '_style':
                    pkg_check_log_data.append(i)
        if pkg_check_log_data != []:
            self.setProperty('pkg_check_log_data', pkg_check_log_data, 'pkg_check_log_data')
        return SUCCESS

class RunEmergeInfo(BuildStep):

    name = 'RunEmergeInfo'
    description = 'Running'
    descriptionDone = 'Ran'
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        aftersteps_list = []
        # add emerge info
        shell_commad_list = [
                    'emerge',
                    ]
        shell_commad_list.append('--info')
        shell_commad_list.append('|')
        shell_commad_list.append('tee')
        shell_commad_list.append('/tmp/emerge_info.txt')
        aftersteps_list.append(
                steps.ShellCommand(
                        name ='emerge --info',
                        # the list need to be joined to pipe to a file
                        command=' '.join(shell_commad_list),
                        workdir='/'
                ))
        # add package info
        cpv = self.getProperty("cpv")
        c = yield catpkgsplit(cpv)[0]
        p = yield catpkgsplit(cpv)[1]
        shell_commad_list = [
                    'emerge',
                    ]
        shell_commad_list.append('-qpvO')
        shell_commad_list.append('=' + self.getProperty('cpv'))
        shell_commad_list.append('--usepkg-exclude')
        shell_commad_list.append(c + '/' + p)
        shell_commad_list.append('|')
        shell_commad_list.append('tee')
        shell_commad_list.append('-a')
        shell_commad_list.append('/tmp/emerge_info.txt')
        aftersteps_list.append(
                steps.ShellCommand(
                        name = 'Package info',
                        # the list need to be joined to pipe to a file
                        command=' '.join(shell_commad_list),
                        workdir='/'
                ))
        yield self.build.addStepsAfterCurrentStep(aftersteps_list)
        return SUCCESS

class RunBuild(BuildStep):

    name = 'Setup steps for building package'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        if not self.getProperty('cpv_build'):
            #FIXME:
            # trigger pars_build_log if we have any logs to check
            return SKIPPED
        aftersteps_list = []
        aftersteps_list.append(RunEmerge(step='pre-build'))
        aftersteps_list.append(RunEmergeInfo())
        aftersteps_list.append(RunEmerge(step='build'))
        aftersteps_list.append(RunEmerge(step='pre-depclean'))
        aftersteps_list.append(RunEmerge(step='preserved-libs'))
        aftersteps_list.append(RunEmerge(step='depclean'))
        self.setProperty('depclean', False, 'depclean')
        self.setProperty('preserved_libs', False, 'preserved-libs')
        yield self.build.addStepsAfterCurrentStep(aftersteps_list)
        return SUCCESS
