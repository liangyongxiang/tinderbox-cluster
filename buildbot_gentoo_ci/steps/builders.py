# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os
import re

from portage.versions import catpkgsplit, cpv_getversion

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
    emerge_output['change_use'] = False
    emerge_output['failed'] = False
    package_dict = {}
    log_path_list = []
    print(stderr)
    # split the lines
    for line in stdout.split('\n'):
        # package list
        subdict = {}
        subdict2 = {}
        if line.startswith('[ebuild') or line.startswith('[binary') or line.startswith('[nomerge'):
            # if binaries
            if line.startswith('[ebuild') or line.startswith('[nomerge'):
                subdict['binary'] = False
            else:
                subdict['binary'] = True
            # action [ N ] stuff
            subdict['action'] = line[8:15].replace(' ', '')
            # cpv
            #FIXME: We my have more then one spece betvine ] and cpv
            cpv_split = re.search('] (.+?) ', line).group(1).split(':')
            print(cpv_split)
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
    emerge_output['package'] = package_dict

    # split the lines
    #FIXME: Handling of stderr output
    stderr_line_list = []
    for line in stderr.split('\n'):
        if 'Change USE:' in line:
            line_list = line.split(' ')
            change_use_list = []
            # get cpv
            cpv_split = line_list[1].split(':')
            change_use_list.append(cpv_split[0])
            # add use flags
            if line_list[4].startswith('+') or line_list[4].startswith('-'):
                # we only support one for now
                if line_list[4].endswith(')'):
                    change_use_list.append(line_list[4].replace(')', ''))
                else:
                    change_use_list = False
            emerge_output['change_use'] = change_use_list
        err_line_list = []
        if line.startswith(' * '):
            if line.endswith('.log.gz'):
                log_path = line.split(' ')[3]
                if log_path not in inlog_path_list:
                    log_path_list.append(log_path)
            stderr_line_list.append(line)
    emerge_output['stderr'] = stderr_line_list
    emerge_output['log_paths'] = log_path_list

    return {
        'emerge_output' : emerge_output
        }

def PersOutputOfPkgCheck(rc, stdout, stderr):
    pkgcheck_output = {}
    pkgcheck_output['rc'] = rc
    #FIXME: Handling of stdout output
    pkgcheck_xml_list = []
    # split the lines
    for line in stdout.split('\n'):
        #  pkgcheck output list
        if line.startswith('<checks'):
            pkgcheck_xml_list.append(line)
        if line.startswith('<result'):
            pkgcheck_xml_list.append(line)
        if line.startswith('</checks'):
            pkgcheck_xml_list.append(line)
    pkgcheck_output['pkgcheck_xml'] = pkgcheck_xml_list
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
                            'project_build_data' : None
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
                    if self.getProperty("version_keyword_dict") is not None:
                        if project_keyword_data['name'] in self.getProperty("version_keyword_dict"):
                            version_keywords_data = self.getProperty("version_keyword_dict")[project_keyword_data['name']]
                            # if match trigger BuildRequest on cpv
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
        repository_data = yield self.gentooci.db.repositorys.getRepositoryByUuid(projectrepository_data['repository_uuid'])
        self.setProperty('project_data', project_data, 'project_data')
        self.setProperty('repository_data', repository_data, 'repository_data')
        self.setProperty('preserved_libs', False, 'preserved-libs')
        self.setProperty('depclean', False, 'depclean')
        self.setProperty('cpv_build', False, 'cpv_build')
        self.setProperty('pkg_check_log_data', None, 'pkg_check_log_data')
        self.setProperty('faild_version_data', None, 'faild_version_data')
        self.setProperty('rerun', 0, 'rerun')
        print(self.getProperty("buildnumber"))
        if self.getProperty('project_build_data') is None:
            project_build_data = {}
            project_build_data['project_uuid'] = project_data['uuid']
            project_build_data['version_uuid'] = self.getProperty("version_data")['uuid']
            project_build_data['status'] = 'in-progress'
            project_build_data['requested'] = False
            project_build_data['buildbot_build_id'] = self.getProperty("buildnumber")
            project_build_data['id'], project_build_data['build_id'] = yield self.gentooci.db.builds.addBuild(
                                                                                            project_build_data)
        else:
            project_build_data = self.getProperty('project_build_data')
            yield self.gentooci.db.builds.setSatusBuilds(
                                                    project_build_data['build_id'],
                                                    project_build_data['project_uuid'],
                                                    'in-progress')
            yield self.gentooci.db.builds.setBuildbotBuildIdBuilds(
                                                    project_build_data['build_id'],
                                                    project_build_data['project_uuid'],
                                                    self.getProperty("buildnumber"))
        self.setProperty('project_build_data', project_build_data, 'project_build_data')
        print(self.getProperty("project_build_data"))
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

class RunEmerge(BuildStep):

    name = 'RunEmerge'
    description = 'Running'
    descriptionDone = 'Ran'
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, step=None,**kwargs):
        self.step = step
        super().__init__(**kwargs)
        self.descriptionSuffix = self.step

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
            # don't build bin for virtual and acct-*
            shell_commad_list.append('--buildpkg-exclude')
            shell_commad_list.append('virtual')
            shell_commad_list.append('--buildpkg-exclude')
            shell_commad_list.append('acct-*')
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
            # don't build bin for virtual and acct-*
            shell_commad_list.append('--buildpkg-exclude')
            shell_commad_list.append('virtual')
            shell_commad_list.append('--buildpkg-exclude')
            shell_commad_list.append('acct-*')
            aftersteps_list.append(
                steps.SetPropertyFromCommandNewStyle(
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=PersOutputOfEmerge,
                        workdir='/',
                        timeout=None
                ))
            aftersteps_list.append(CheckEmergeLogs('update'))
            if projects_emerge_options['preserved_libs']:
                self.setProperty('preserved_libs', True, 'preserved-libs')

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
                steps.SetPropertyFromCommandNewStyle(
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=PersOutputOfDepclean,
                        workdir='/'
                ))
            aftersteps_list.append(CheckDepcleanLogs('depclean'))

        if self.step == 'match':
            cpv = self.getProperty("cpv")
            c = yield catpkgsplit(cpv)[0]
            p = yield catpkgsplit(cpv)[1]
            shell_commad_list.append('-pO')
            # don't use bin for match
            shell_commad_list.append('--usepkg=n')
            shell_commad_list.append(c + '/' + p)
            aftersteps_list.append(
                steps.SetPropertyFromCommandNewStyle(
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=PersOutputOfEmerge,
                        workdir='/',
                        timeout=None
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
                steps.SetPropertyFromCommandNewStyle(
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=PersOutputOfEmerge,
                        workdir='/',
                        timeout=None
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
                steps.SetPropertyFromCommandNewStyle(
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=PersOutputOfEmerge,
                        workdir='/',
                        timeout=None
                ))
            aftersteps_list.append(CheckEmergeLogs('build'))
            if projects_emerge_options['preserved_libs']:
                self.setProperty('preserved_libs', True, 'preserved-libs')

        if not self.step is None and aftersteps_list != []:
            yield self.build.addStepsAfterCurrentStep(aftersteps_list)
        return SUCCESS

class CheckEmergeLogs(BuildStep):

    name = 'CheckEmergeLogs'
    description = 'Running'
    descriptionDone = 'Ran'
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, step=None,**kwargs):
        self.step = step
        super().__init__(**kwargs)
        self.descriptionSuffix = self.step
        self.aftersteps_list = []
        self.log_data = {}

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
    def getLogFile(self, cpv, log_dict):
        masterdest = yield os.path.join(self.master.basedir, 'cpv_logs', log_dict[cpv]['full_logname'])
        self.aftersteps_list.append(steps.FileUpload(
            workersrc=log_dict[cpv]['log_path'],
            masterdest=masterdest
        ))

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

        #FIXME: Prosees the logs and do stuff
        # preserved-libs
        if emerge_output['preserved_libs'] and projects_emerge_options['preserved_libs']:
            self.setProperty('preserved_libs', True, 'preserved-libs')

        # FIXME: check if cpv match
        if self.step == 'match'and self.getProperty('projectrepository_data')['build']:
            if self.getProperty('cpv') in emerge_output['package']:
                self.setProperty('cpv_build', True, 'cpv_build')
            print(self.getProperty('cpv_build'))

        #FIXME:
        # update package.* if needed and rerun pre-build max 3 times
        if self.step == 'pre-build':
            print(emerge_output)
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
                    cpv = emerge_output['change_use'][0]
                    c = yield catpkgsplit(cpv)[0]
                    p = yield catpkgsplit(cpv)[1]
                    change_use_list.append(c + '/' + p)
                    # we only support one use
                    use_flag = emerge_output['change_use'][1]
                    if use_flag.startswith('+'):
                        change_use_list.append(use_flag.replace('+', ''))
                    else:
                        change_use_list.append(use_flag)
                    change_use_string = separator2.join(change_use_list)
                    self.aftersteps_list.append(
                        steps.StringDownload(change_use_string + separator,
                                workerdest='zz_autouse' + str(self.getProperty('rerun')),
                                workdir='/etc/portage/package.use/')
                        )
                    # rerun
                    self.aftersteps_list.append(RunEmerge(step='pre-build'))
                    self.setProperty('rerun', self.getProperty('rerun') + 1, 'rerun')
            else:
                # trigger parse_build_log with info about pre-build and it fail
                pass
        #FIXME:
        # Look for FAILURE and logname and download needed logfile and
        # trigger a logparser
        # local_log_path dir set in config
        # format /var/cache/portage/logs/build/gui-libs/egl-wayland-1.1.6:20210321-173525.log.gz
        if self.step == 'build':
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
            # Find log for cpv that was requested or did failed
            if not log_dict == {}:
                # requested cpv
                print(log_dict)
                cpv = self.getProperty('cpv')
                faild_cpv = emerge_output['failed']
                if cpv in log_dict or faild_cpv in log_dict:
                    if cpv in log_dict:
                        self.log_data[cpv] = log_dict[cpv]
                        yield self.getLogFile(cpv, log_dict)
                        faild_version_data = False
                    if faild_cpv:
                        # failed and build requested cpv
                        if cpv == faild_cpv:
                            faild_version_data = self.getProperty("version_data")
                        else:
                            # failed but not build requested cpv
                            self.log_data[faild_cpv] = log_dict[faild_cpv]
                            yield self.getLogFile(faild_cpv, log_dict)
                            faild_version_data = yield self.getVersionData(faild_cpv)
                    self.aftersteps_list.append(steps.Trigger(
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
                            'faild_cpv' : faild_cpv,
                            'step' : self.step
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

    name = 'RunPkgCheck'
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
        shell_commad_list.append('XmlReporter')
        aftersteps_list = []
        if projectrepository_data['pkgcheck'] == 'full':
            pkgcheck_workdir = yield os.path.join(repository_path, '')
        else:
            pkgcheck_workdir = yield os.path.join(repository_path, c, p, '')
        aftersteps_list.append(
            steps.SetPropertyFromCommandNewStyle(
                        command=shell_commad_list,
                        strip=True,
                        extract_fn=PersOutputOfPkgCheck,
                        workdir=pkgcheck_workdir
            ))
        aftersteps_list.append(CheckPkgCheckLogs())
        yield self.build.addStepsAfterCurrentStep(aftersteps_list)
        return SUCCESS

class CheckPkgCheckLogs(BuildStep):

    name = 'CheckPkgCheckLogs'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    #@defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        project_data = self.getProperty('project_data')
        pkgcheck_output = self.getProperty('pkgcheck_output')
        print(pkgcheck_output)
        #FIXME:
        # Perse the logs
        self.setProperty('pkg_check_log_data', None, 'pkg_check_log_data')
        return SUCCESS

class RunBuild(BuildStep):

    name = 'RunBuild'
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
            return SUCCESS
        aftersteps_list = []
        aftersteps_list.append(RunEmerge(step='pre-build'))
        aftersteps_list.append(RunEmerge(step='build'))
        self.setProperty('depclean', False, 'depclean')
        self.setProperty('preserved_libs', False, 'preserved-libs')
        yield self.build.addStepsAfterCurrentStep(aftersteps_list)
        return SUCCESS
