# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

#from buildbot import reporters as buildbot_reporters
from buildbot.reporters.generators.build import BuildStatusGenerator
from buildbot.reporters.message import MessageFormatter

from buildbot_gentoo_ci.reporters import irc
#FIXME can colors be added here or is it needed in IRCStatusPush
irc_template = '''\
Buildbot: {{ build['properties']['cpv'][0] }} repo/{{ projects }} {{ build['properties']['revision'][0] }} \
{{ build['properties']['owners'][0] }} {{ build['properties']['project_data'][0]['name'] }} {{ summary }} {{ build_url }}\
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
                 useColors=False,
                 channels=[{"channel": "#gentoo-ci"},
                        ],
                 generators=ircGenerators()
                 )

def gentoo_reporters(r=[]):
    r.append(irc_reporter)
    return r
