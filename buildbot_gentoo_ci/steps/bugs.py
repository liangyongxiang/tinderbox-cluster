# Copyright 2022 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import re

from twisted.internet import defer

from buildbot.process.buildstep import BuildStep
from buildbot.process.results import SUCCESS
from buildbot.process.results import FAILURE
from buildbot.process.results import SKIPPED

from bugz.cli import check_bugz_token, login, list_bugs
from bugz.cli_argparser import make_arg_parser
from bugz.configfile import load_config
from bugz.settings import Settings
from bugz.exceptions import BugzError
from bugz.log import log_error, log_info

from portage.versions import cpv_getversion, pkgsplit, catpkgsplit

# Origins: bugz.cli
# Modifyed by Gentoo Authors.
# main
def main_bugz(args):
    ArgParser = make_arg_parser()
    opt = ArgParser.parse_args(args)

    ConfigParser = load_config(getattr(opt, 'config_file', None))

    check_bugz_token()
    settings = Settings(opt, ConfigParser)
    return settings

# search
def search_bugz(args):
    settings = main_bugz(args)
    valid_keys = ['alias', 'assigned_to', 'component', 'creator',
                'limit', 'offset', 'op_sys', 'platform',
                'priority', 'product', 'resolution', 'severity',
                'version', 'whiteboard', 'cc']

    params = {}
    d = vars(settings)
    for key in d:
        if key in valid_keys:
            params[key] = d[key]
    if 'search_statuses' in d:
        if 'all' not in d['search_statuses']:
            params['status'] = d['search_statuses']
    if 'terms' in d:
        params['summary'] = d['terms']

    if not params:
        raise BugzError('Please give search terms or options.')

    log_info('Searching for bugs meeting the following criteria:')
    for key in params:
        log_info('   {0:<20} = {1}'.format(key, params[key]))

    login(settings)

    result = settings.call_bz(settings.bz.Bug.search, params)['bugs']

    if not len(result):
        log_info('No bugs found.')
        return []
    else:
        list_bugs(result, settings)
        return result

class GetBugs(BuildStep):
    
    name = 'GetBugs'
    description = 'Running'
    descriptionDone = 'Ran'
    descriptionSuffix = None
    haltOnFailure = True
    flunkOnFailure = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @defer.inlineCallbacks
    def find_match(self, buglist):
        log = yield self.addLog('Bugs')
        yield log.addStdout('Open Bugs\n')
        match = False
        for bug in buglist:
            yield log.addStdout('Bug: ' + str(bug['id']) + ' Summary: ' + bug['summary'] +'\n')
            if re.search(self.getProperty('error_dict')['title_issue'][:20], bug['summary']):
                print('Bug found')
                print(bug)
                match = {}
                match['id'] = bug['id']
                match['summary'] = bug['summary']
        if match:
            yield log.addStdout('Match bug found\n')
            yield log.addStdout('Bug: ' + str(match['id']) + ' Summary: ' + match['summary'] +'\n')
            self.setProperty("bgo", match, 'bgo')
            return
        yield log.addStdout('NO Match bug found\n')
        self.setProperty("bgo", False, 'bgo')

    @defer.inlineCallbacks
    def run(self):
        # self.gentooci = self.master.namedServices['services'].namedServices['gentooci']
        cpv = self.getProperty('error_dict')['cpv']
        c = yield catpkgsplit(cpv)[0]
        p = yield catpkgsplit(cpv)[1]
        cp = c + '/' + p
        # search for open bugs
        args = []
        args.append('--skip-auth')
        args.append('search')
        # set limit
        # set date last 30 days
        # search for cp
        args.append(cp)
        print(args)
        buglist = search_bugz(args)
        print(buglist)
        self.find_match(buglist)
        return SUCCESS
