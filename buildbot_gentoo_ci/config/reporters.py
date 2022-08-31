# Copyright 2022 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from buildbot.plugins import util
from buildbot.reporters.gitlab import GitLabStatusPush
from buildbot.reporters.generators.build import BuildStatusGenerator, BuildStartEndStatusGenerator
from buildbot.reporters.message import MessageFormatter

from buildbot_gentoo_ci.reporters import irc
irc_template = '''{% set resultsList = ["\x0303SUCCESS", "\x0308WARNINGS", "\x0304FAILURE"] %}\
{{ "\x02" }}{{ build['properties']['cpv'][0] }}{{ "\x02" }} {{ "\x0303" }}Repo:{{ projects }}:{{ build['properties']['branch'][0] }}{{ "\x03" }} \
{{ build['properties']['revision'][0]|truncate(10, True) }} {{ "\x0302" }}{{ build['properties']['owners'][0][0] }}{{ "\x03" }} \
{{ "\x0306" }}{{ build['properties']['event'][0] }}{{ "\x03" }} {{ projects }}:{{ build['properties']['project_data'][0]['name'] }} \
{{ "\x02" }}{{ "Build: "}}{{ resultsList[build['results']] }}{{ "\x03" }}{{ "\x02" }} {{ "\x0312" }}{{ build_url }}{{ "\x03" }} \
{% if build['properties']['bgo'][0]['match'] is true %}{{ "\x0311" }}Bugid: {{build['properties']['bgo'][0]['id']}}{{ "\x03" }}{% endif %}\
'''

def ircGenerators():
    formatter = MessageFormatter(
        template=irc_template
    )
    builders = [
        'parse_build_log'
    ]
    mode = [
        'failing',
        'warnings',
    ]
    return [
        BuildStatusGenerator(
            message_formatter=formatter,
            builders=builders,
            mode=mode
        )
    ]
#FIXME:
# server, nick channel should be set in config
irc_reporter = irc.IRCStatusPush("irc.libera.chat", "gci_test",
                 channels=[{"channel": "#gentoo-ci"},
                        ],
                 generators=ircGenerators(),
                 noticeOnChannel=True
                 )
#gitlab
def gitlabGenerators():
    builders = [
        #'run_build_request',
        'parse_build_log'
    ]
    return [
        BuildStartEndStatusGenerator(
            builders=builders
        )
    ]
gitlab_gentoo_org = GitLabStatusPush(token=util.Secret("gitlabToken"),
                                #context= util.Interpolate('Buildbot %(prop:buildername)s'),
                                baseURL='https://gitlab.gentoo.org',
                                generators=gitlabGenerators(),
                                #debug=True,
                                verbose=True
                                )

def gentoo_reporters(r=[]):
    #r.append(irc_reporter)
    r.append(gitlab_gentoo_org)
    return r
