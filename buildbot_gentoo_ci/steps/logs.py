# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import os
import re
import gzip
import io
import hashlib

from portage.versions import catpkgsplit

from twisted.internet import defer
from twisted.python import log

from buildbot.process.buildstep import BuildStep
from buildbot.process.results import SUCCESS
from buildbot.process.results import FAILURE
from buildbot.process.results import WARNINGS
from buildbot.plugins import steps

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
        default_project_data = yield self.gentooci.db.projects.getProjectByName(self.gentooci.config.project['project'])
        version_data = yield self.gentooci.db.versions.getVersionByUuid(self.getProperty('project_build_data')['version_uuid'])
        self.setProperty("project_data", project_data, 'project_data')
        self.setProperty("default_project_data", default_project_data, 'default_project_data')
        self.setProperty("version_data", version_data, 'version_data')
        self.setProperty("status", 'completed', 'status')
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
        file_path = yield os.path.join(self.master.basedir, 'cpv_logs', log_cpv['full_logname'])
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

    #@defer.inlineCallbacks
    def run(self):
        self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        summary_log_dict = self.getProperty('summary_log_dict')
        error = False
        warning = False
        self.summary_log_list = []
        log_hash = hashlib.sha256()
        for k, v in sorted(summary_log_dict.items()):
            if v['status'] == 'error':
                error = True
            if v['status'] == 'warning':
                warning = True
            self.summary_log_list.append(v['text'])
            log_hash.update(v['text'].encode('utf-8'))
        # add build log
        # add issue/bug/pr report
        self.setProperty("summary_log_list", self.summary_log_list, 'summary_log_list')
        if error:
            self.setProperty("status", 'failed', 'status')
        if warning:
            self.setProperty("status", 'warning', 'status')
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
        # add emerge info log
        return SUCCESS

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
                                                    project_build_data['build_id'],
                                                    project_build_data['project_uuid'],
                                                    self.getProperty('status')
                                                    )
        if self.getProperty('status') == 'failed':
            return FAILURE
        if self.getProperty('status') == 'warning':
            return WARNINGS
        return SUCCESS
