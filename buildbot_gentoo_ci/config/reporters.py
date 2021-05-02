# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

#from buildbot import reporters as buildbot_reporters
from buildbot.reporters.generators.build import BuildStatusGenerator
from buildbot.reporters.message import MessageFormatter

from buildbot_gentoo_ci.reporters import irc
irc_template = '''{% set resultsList = ["\x0303SUCCESS", "\x0308WARNINGS", "\x0304FAILURE"] %}\
Buildbot: {{ "\x02" }}{{ build['properties']['cpv'][0] }}{{ "\x02" }} {{ "\x0303" }}repo/{{ projects }}{{ "\x03" }} \
{{ build['properties']['revision'][0]|truncate(10, True) }} {{ "\x0302" }}{{ build['properties']['owners'][0][0] }}{{ "\x03" }} \
{{ build['properties']['project_data'][0]['name'] }} \
{{ "\x02" }}{{ "Build: "}}{{ resultsList[build['results']] }}{{ "\x03" }}{{ "\x02" }} {{ "\x0312" }}{{ build_url }}{{ "\x03" }}\
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
        'passing',
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
irc_reporter = irc.IRCStatusPush("irc.freenode.net", "gentoo_ci_test",
                 channels=[{"channel": "#gentoo-ci"},
                        ],
                 generators=ircGenerators()
                 )

def gentoo_reporters(r=[]):
    r.append(irc_reporter)
    return r
