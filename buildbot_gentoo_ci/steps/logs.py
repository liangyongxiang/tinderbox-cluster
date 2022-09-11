# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os
import re
import gzip
import io
import hashlib
import json

from portage.versions import catpkgsplit

from twisted.internet import defer
from twisted.python import log

from buildbot.process.buildstep import BuildStep
from buildbot.process.results import SUCCESS
from buildbot.process.results import FAILURE
from buildbot.process.results import WARNINGS
from buildbot.process.results import SKIPPED
from buildbot.plugins import steps

#from buildbot_gentoo_ci.steps import minio
from buildbot_gentoo_ci.steps import master as master_steps
from buildbot_gentoo_ci.steps import bugs

def PersOutputOfLogParser(rc, stdout, stderr):
    build_summery_output = {}
    build_summery_output['rc'] = rc
    summary_log_dict = {}
    # split the lines
    for line in stdout.split('\n'):
        #FIXME: check if line start with {"[1-9]": {
        if line.startswith('{'):
            for k, v in json.loads(line).items():
                summary_log_dict[int(k)] = {
                                    'text' : v['text'],
                                    'type' : v['type'],
                                    'status' : v['status'],
                                    'id' : v['id'],
                                    'search_pattern' : v['search_pattern']
                                    }
    build_summery_output['summary_log_dict'] = summary_log_dict
    #FIXME: Handling of stderr output
    return {
        'build_summery_output' : build_summery_output
        }

def PersOutputOfEmergeInfo(rc, stdout, stderr):
    #FIXME: line for package info
    emerge_info_output = {}
    emerge_info_output['rc'] = rc
    emerge_info_list = []
    emerge_package_info = []
    for line in stdout.split('\n'):
        if line.startswith('['):
            emerge_package_info.append(line)
        else:
            emerge_info_list.append(line)
    emerge_info_output['emerge_info'] = emerge_info_list
    emerge_info_output['emerge_package_info'] = emerge_package_info
    return {
        'emerge_info_output' : emerge_info_output
        }

class SetupPropertys(BuildStep):
    
    name = 'SetupPropertys'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        # set this in config
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        project_data = yield self.gentooci.db.projects.getProjectByUuid(self.getProperty('project_build_data')['project_uuid'])
        default_project_data = yield self.gentooci.db.projects.getProjectByName(self.gentooci.config.project['project']['update_db'])
        version_data = yield self.gentooci.db.versions.getVersionByUuid(self.getProperty('project_build_data')['version_uuid'])
        self.setProperty("project_data", project_data, 'project_data')
        self.setProperty("default_project_data", default_project_data, 'default_project_data')
        self.setProperty("version_data", version_data, 'version_data')
        self.setProperty("status", 'completed', 'status')
        if self.getProperty('faild_cpv'):
            log_cpv = self.getProperty('faild_cpv')
        else:
            log_cpv = self.getProperty('cpv')
        self.setProperty("log_cpv", log_cpv, 'log_cpv')
        self.setProperty("bgo", dict( match=False), 'bgo')
        self.descriptionDone = 'Runing log checker on ' + log_cpv
        return SUCCESS

class SetupParserBuildLoger(BuildStep):

    name = 'SetupParserBuildLoger'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.aftersteps_list = []
        workdir = yield os.path.join(self.master.basedir, 'workers', self.getProperty('build_workername'), str(self.getProperty("project_build_data")['buildbot_build_id']))
        log_cpv = self.getProperty('log_build_data')[self.getProperty('log_cpv')]
        mastersrc_log = yield os.path.join(workdir, log_cpv['full_logname'])
        log_py = 'py/log_parser.py'
        config_log_py = 'logparser.json'
        mastersrc_py = yield os.path.join(self.master.basedir, log_py)
        mastersrc_config = yield os.path.join(self.master.basedir, config_log_py)
        # Upload logfile to worker
        self.aftersteps_list.append(steps.FileDownload(
                                                    mastersrc=mastersrc_log,
                                                    workerdest=log_cpv['full_logname']
                                                    ))
        # Upload log parser py code
        self.aftersteps_list.append(steps.FileDownload(
                                                    mastersrc=mastersrc_py,
                                                    workerdest=log_py
                                                    ))
        # Upload log parser py config
        self.aftersteps_list.append(steps.FileDownload(
                                                    mastersrc=mastersrc_config,
                                                    workerdest=config_log_py
                                                    ))
        # Run the log parser code
        command = []
        command.append('python3')
        command.append(log_py)
        command.append('-f')
        command.append(log_cpv['full_logname'])
        command.append('-u')
        command.append(self.getProperty('project_data')['uuid'])
        self.aftersteps_list.append(steps.SetPropertyFromCommand(
                                                            name = 'RunBuildLogParser',
                                                            haltOnFailure = True,
                                                            flunkOnFailure = True,
                                                            command=command,
                                                            strip=False,
                                                            extract_fn=PersOutputOfLogParser,
                                                            timeout=3600
                                                            ))
        yield self.build.addStepsAfterCurrentStep(self.aftersteps_list)
        return SUCCESS

class ParserBuildLog(BuildStep):

    name = 'ParserBuildLog'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        self.logfile_text_dict = {}
        self.summery_dict = {}
        self.index = 1
        self.log_search_pattern_list = []
        self.max_text_lines = 0
        super().__init__(**kwargs)

    #FIXME: ansifilter
    def ansiFilter(self, text):
        return text

    @defer.inlineCallbacks
    def get_log_search_pattern(self):
        # get pattern from the projects
        # add that to log_search_pattern_list
        for project_pattern in (yield self.gentooci.db.projects.getProjectLogSearchPatternByUuid(self.getProperty('project_data')['uuid'])):
            # check if the search pattern is vaild
            try:
                re.compile(project_pattern['search'])
            except re.error:
                print("Non valid regex pattern")
                print(project_pattern)
            else:
                self.log_search_pattern_list.append(project_pattern)
        # get the default project pattern
        # add if not pattern is in project ignore
        self.project_pattern_ignore = yield self.gentooci.db.projects.getProjectLogSearchPatternByUuidAndIgnore(self.getProperty('project_data')['uuid'])
        for project_pattern in (yield self.gentooci.db.projects.getProjectLogSearchPatternByUuid(self.getProperty('default_project_data')['uuid'])):
            if not project_pattern['search'] in self.project_pattern_ignore:
                # check if the search pattern is vaild
                try:
                    re.compile(project_pattern['search'])
                except re.error:
                    print("Non valid regex pattern")
                    print(project_pattern)
                else:
                    self.log_search_pattern_list.append(project_pattern)

    def search_buildlog(self, tmp_index):
        # get text line to search
        text_line = self.ansiFilter(self.logfile_text_dict[tmp_index])
        # loop true the pattern list for match
        for search_pattern in self.log_search_pattern_list:
            search_hit = False
            if search_pattern['search_type'] == 'in':
                if search_pattern['search'] in text_line:
                    search_hit = True
            if search_pattern['search_type'] == 'startswith':
                if text_line.startswith(search_pattern['search']):
                    search_hit = True
            if search_pattern['search_type'] == 'endswith':
                if text_line.endswith(search_pattern['search']):
                    search_hit = True
            if search_pattern['search_type'] == 'search':
                if re.search(search_pattern['search'], text_line):
                    search_hit = True
            # add the line if the pattern match
            if search_hit:
                print(text_line)
                print(search_pattern)
                print(tmp_index)
                self.summery_dict[tmp_index] = {}
                self.summery_dict[tmp_index]['text'] = text_line
                self.summery_dict[tmp_index]['type'] = search_pattern['type']
                self.summery_dict[tmp_index]['status'] = search_pattern['status']
                self.summery_dict[tmp_index]['search_pattern_id'] = search_pattern['id']
                # add upper text lines if requested
                # max 5
                if search_pattern['start'] != 0:
                    i = tmp_index - search_pattern['start'] - 1
                    match = True
                    while match:
                        i = i + 1
                        if i < (tmp_index - 9) or i == tmp_index:
                            match = False
                        else:
                            if not i in self.summery_dict:
                                self.summery_dict[i] = {}
                                self.summery_dict[i]['text'] = self.ansiFilter(self.logfile_text_dict[i])
                                self.summery_dict[i]['type'] = 'info'
                                self.summery_dict[i]['status'] = 'info'
                # add lower text lines if requested
                # max 5
                if search_pattern['end'] != 0:
                    i = tmp_index
                    end = tmp_index + search_pattern['end']
                    match = True
                    while match:
                        i = i + 1
                        if i > self.max_text_lines or i > end:
                            match = False
                        else:
                            if not i in self.summery_dict:
                                self.summery_dict[i] = {}
                                self.summery_dict[i]['text'] = self.ansiFilter(self.logfile_text_dict[i])
                                self.summery_dict[i]['type'] = 'info'
                                self.summery_dict[i]['status'] = 'info'
            else:
                # we add all line that start with ' * ' as info
                # we add all line that start with '>>>' but not '>>> /' as info
                if text_line.startswith(' * ') or (text_line.startswith('>>>') and not text_line.startswith('>>> /')):
                    if not tmp_index in self.summery_dict:
                        self.summery_dict[tmp_index] = {}
                        self.summery_dict[tmp_index]['text'] = text_line
                        self.summery_dict[tmp_index]['type'] = 'info'
                        self.summery_dict[tmp_index]['status'] = 'info'

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        yield self.get_log_search_pattern()
        # open the log file
        # read it to a buffer
        # make a dict of the buffer
        # maybe use mulitiprocces to speed up the search
        print(self.getProperty('log_build_data'))
        if self.getProperty('faild_cpv'):
            log_cpv = self.getProperty('log_build_data')[self.getProperty('faild_cpv')]
        else:
            log_cpv = self.getProperty('log_build_data')[self.getProperty('cpv')]
        file_path = yield os.path.join(self.master.basedir, 'workers', self.getProperty('build_workername'), str(self.getProperty("project_build_data")['buildbot_build_id']) ,log_cpv['full_logname'])
        #FIXME: decode it to utf-8
        with io.TextIOWrapper(io.BufferedReader(gzip.open(file_path, 'rb'))) as f:
            for text_line in f:
                self.logfile_text_dict[self.index] = text_line.strip('\n')
                # run the parse patten on the line
                # have a buffer on 10 before we run pattern check
                if self.index >= 10:
                    yield self.search_buildlog(self.index - 9)
                # remove text line that we don't need any more
                if self.index >= 20:
                    del self.logfile_text_dict[self.index - 19]
                self.index = self.index + 1
                self.max_text_lines = self.index
            f.close()
        # check last 10 lines in logfile_text_dict
        yield self.search_buildlog(self.index - 10)
        print(self.summery_dict)
        # remove all lines with ignore in the dict
        # setProperty summery_dict
        self.setProperty("summary_log_dict", self.summery_dict, 'summary_log_dict')
        return SUCCESS

class MakeIssue(BuildStep):

    name = 'MakeIssue'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def logIssue(self):
        separator1 = '\n'
        separator2 = ' '
        log = yield self.addLog('issue')
        self.error_dict['cpv'] = self.getProperty('log_cpv')
        yield log.addStdout('Title:' + '\n')
        yield log.addStdout(separator2.join([self.getProperty('log_cpv'), '-', self.error_dict['title']]) + separator1)
        yield log.addStdout('Summary:' + '\n')
        for line in self.summary_log_list:
            yield log.addStdout(line + '\n')
        yield log.addStdout('Attachments:' + '\n')
        yield log.addStdout('emerge_info.log' + '\n')
        log_cpv = self.getProperty('log_build_data')[self.getProperty('log_cpv')]
        yield log.addStdout(log_cpv['full_logname'] + '\n')
        yield log.addStdout('world.log' + '\n')

    def getNiceErrorLine(self, line):
        # strip away hex addresses, loong path names, line and time numbers and other stuff
        # https://github.com/toralf/tinderbox/blob/main/bin/job.sh#L467
        # FIXME: Add the needed line when needed
        if re.search(': line', line):
            line = re.sub(r"\d", "<snip>", line)
        # Shorten the path
        if line.startswith('/usr/'):
            line = line.replace(os.path.split(line.split(' ', 1)[0])[0], '/...')
        if re.search(': \d:\d: ', line):
            line = re.sub(r":\d:\d: ", ": ", line)
        return line

    def ClassifyIssue(self):
        # get the title for the issue
        text_issue_list = []
        text_phase_list = []
        for k, v in sorted(self.summary_log_dict.items()):
            # get the issue error
            if v['type'] == self.error_dict['phase'] and v['status'] == 'error':
                text_issue_list.append(v['text'])
        # add the issue error
        if text_issue_list != []:
            self.error_dict['title_issue'] = text_issue_list[0].replace('*', '').strip()
            self.error_dict['title_issue_nice'] = self.getNiceErrorLine(text_issue_list[0].replace('*', '').strip())
        else:
            self.error_dict['title_issue'] = 'title_issue : None'
            self.error_dict['title_nice'] = 'title_issue : None'
        self.error_dict['title_phase'] = 'failed in '+ self.error_dict['phase']
        #set the error title
        self.error_dict['title'] = self.error_dict['title_phase'] + ' - ' + self.error_dict['title_issue']

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        self.summary_log_dict = self.getProperty('build_summery_output')['summary_log_dict']
        error = False
        warning = False
        self.summary_log_list = []
        self.error_dict = {}
        self.aftersteps_list = []
        #self.error_dict['hash'] = hashlib.sha256()
        for k, v in sorted(self.summary_log_dict.items()):
            self.summary_log_list.append(v['text'])
            #self.error_dict['hash'].update(v['text'].encode('utf-8'))
            if v['status'] == 'warning':
                warning = True
            # check if the build did fail
            if v['text'].startswith(' * ERROR:') and v['text'].endswith(' phase):'):
                # get phase error
                phase_error = v['text'].split(' (')[1].split(' phase')[0]
                self.error_dict['phase'] = phase_error
                error = True
        # add build log
        # add issue/bug/pr report
        if error:
            yield self.ClassifyIssue()
            print(self.error_dict)
            yield self.logIssue()
            self.setProperty("status", 'failed', 'status')
            self.setProperty("error_dict", self.error_dict, 'error_dict')
            self.aftersteps_list.append(bugs.GetBugs())
        if warning:
            self.setProperty("status", 'warning', 'status')
            self.setProperty("bgo", False, 'bgo')
        self.setProperty("summary_log_list", self.summary_log_list, 'summary_log_list')
        if self.aftersteps_list is not []:
            yield self.build.addStepsAfterCurrentStep(self.aftersteps_list)
        return SUCCESS

class setBuildbotLog(BuildStep):

    name = 'setBuildbotLog'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = False
    flunkOnFailure = True
    warnOnWarnings = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        #setup the log
        log = yield self.addLog('summary')
        # add line for line
        for line in self.getProperty('summary_log_list'):
            yield log.addStdout(line + '\n')
        return SUCCESS

class ReadEmergeInfoLog(BuildStep):

    name = 'ReadEmergeInfoLog'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = False
    flunkOnFailure = True
    warnOnWarnings = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        emerge_info_output = {}
        emerge_info_list = []
        emerge_package_info = []
        # Read the file and add it to a property
        workdir = yield os.path.join(self.master.basedir, 'workers', self.getProperty('build_workername'), str(self.getProperty("project_build_data")['buildbot_build_id']))
        with open(os.path.join(workdir, 'emerge_info.txt'), encoding='utf-8') as source:
            emerge_info = source.read()
        # set emerge_info_output Property
        for line in emerge_info.split('\n'):
            if line.startswith('['):
                emerge_package_info.append(line)
            else:
                emerge_info_list.append(line)
        emerge_info_output['emerge_info'] = emerge_info_list
        emerge_info_output['emerge_package_info'] = emerge_package_info
        self.setProperty("emerge_info_output", emerge_info_output, 'emerge_info_output')
        return SUCCESS

class setEmergeInfoLog(BuildStep):

    name = 'setEmergeInfoLog'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = False
    flunkOnFailure = True
    warnOnWarnings = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        #setup the log
        log = yield self.addLog('emerge_info')
        #FIXME: add emerge info to db
        # add line for line
        for line in self.getProperty('emerge_info_output')['emerge_info']:
            yield log.addStdout(line + '\n')
        return SUCCESS

class setPackageInfoLog(BuildStep):

    name = 'setPackageInfoLog'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = False
    flunkOnFailure = True
    warnOnWarnings = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        #setup the log
        log = yield self.addLog('package_info')
        #FIXME: add package info to db
        # add line for line
        for line in self.getProperty('emerge_info_output')['emerge_package_info']:
            yield log.addStdout(line + '\n')
        return SUCCESS


class Upload(BuildStep):

    name = 'Upload'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = False
    flunkOnFailure = True
    warnOnWarnings = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        log_cpv = self.getProperty('log_build_data')[self.getProperty('log_cpv')]
        bucket = self.getProperty('project_data')['uuid'] + '-' + 'logs'
        file_path = yield os.path.join(self.master.basedir, 'workers', self.getProperty('build_workername'), str(self.getProperty("project_build_data")['buildbot_build_id']) ,log_cpv['full_logname'])
        aftersteps_list = []
        #aftersteps_list.append(minio.putFileToMinio(file_path, log_cpv['full_logname'], bucket))
        #yield self.build.addStepsAfterCurrentStep(aftersteps_list)
        return SUCCESS

class ParserPkgCheckLog(BuildStep):

    name = 'ParserPkgCheckLog'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = False
    flunkOnWarnings = False
    flunkOnFailure = False
    warnOnWarnings = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        if self.getProperty("pkg_check_log_data") is None:
            return SKIPPED
        returnstatus = SUCCESS
        error = False
        warning = False
        log = yield self.addLog('Pkgcheck')
        print(self.getProperty("pkg_check_log_data"))
        for a in self.getProperty("pkg_check_log_data"):
            status = ''
            print(a)
            if isinstance(a, dict):
                for k, i in a.items():
                    if k.startswith('_'):
                        if k == '_info':
                            status = 'INFO: '
                        if k == '_error':
                            status = 'ERROR: '
                            error = True
                        if k == '_warning':
                            status = 'WARNING: '
                            warning = True
                        if k == '_style':
                            status = 'STYLE: '
                        if isinstance(i, dict):
                            for b, c in i.items():
                                yield log.addStdout(status + b + c + '\n')
                    else:
                        yield log.addStdout(i + '\n')
        if error:
            returnstatus = FAILURE
        if warning and not error:
            returnstatus = WARNINGS
        return returnstatus

class setBuildStatus(BuildStep):

    name = 'setBuildStatus'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = False
    flunkOnFailure = True
    warnOnWarnings = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        project_build_data = self.getProperty('project_build_data')
        yield self.gentooci.db.builds.setSatusBuilds(
                                                    project_build_data['id'],
                                                    self.getProperty('status')
                                                    )
        if self.getProperty('status') == 'failed':
            return FAILURE
        if self.getProperty('status') == 'warning':
            return WARNINGS
        return SUCCESS
