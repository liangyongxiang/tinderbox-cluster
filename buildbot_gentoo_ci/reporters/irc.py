# This file has parts from Buildbot and is modifyed by Gentoo Authors. 
# Buildbot is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License as published by the 
# Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright Buildbot Team Members
# Origins: buildbot.reporters.irc.py
# Modifyed by Gentoo Authors.
# Copyright 2021 Gentoo Authors

from twisted.application import internet
from twisted.internet import defer
from twisted.python import log
from twisted.words.protocols import irc
from twisted.words.protocols.irc import assembleFormattedText, attributes as A

from buildbot import config
from buildbot.reporters.irc import IrcStatusFactory
from buildbot.util import service
from buildbot.util import ssl

from buildbot.reporters.base import ReporterBase
from buildbot.reporters.generators.build import BuildStatusGenerator
from buildbot.reporters.message import MessageFormatterRenderable

class UsageError(ValueError):

    # pylint: disable=useless-super-delegation
    def __init__(self, string="Invalid usage", *more):
        # This is not useless as we change the default value of an argument.
        # This bug is reported as "fixed" but apparently, it is not.
        # https://github.com/PyCQA/pylint/issues/1085
        # (Maybe there is a problem with builtin exceptions).
        super().__init__(string, *more)

class IRCStatusPush(ReporterBase):
    name = "IRCStatusPush"
    in_test_harness = False
    f = None
    compare_attrs = ("host", "port", "nick", "password", "authz",
                     "channels", "pm_to_nicks", "useSSL",
                     "useRevisions", "tags", "useColors",
                     "allowForce", "allowShutdown",
                     "lostDelay", "failedDelay")
    secrets = ['password']

    def checkConfig(self, host, nick, channels, pm_to_nicks=None, port=6667,
                    allowForce=None, tags=None, password=None, generators=None,
                    showBlameList=True, useRevisions=False,
                    useSSL=False, lostDelay=None, failedDelay=None, useColors=False,
                    allowShutdown=None, noticeOnChannel=False, authz=None, **kwargs
                    ):
        deprecated_params = list(kwargs)
        if deprecated_params:
            config.error("{} are deprecated".format(",".join(deprecated_params)))

        # deprecated
        if allowForce is not None:
            if authz is not None:
                config.error("If you specify authz, you must not use allowForce anymore")
            if allowForce not in (True, False):
                config.error("allowForce must be boolean, not %r" % (allowForce,))
            log.msg('IRC: allowForce is deprecated: use authz instead')
        if allowShutdown is not None:
            if authz is not None:
                config.error("If you specify authz, you must not use allowShutdown anymore")
            if allowShutdown not in (True, False):
                config.error("allowShutdown must be boolean, not %r" %
                             (allowShutdown,))
            log.msg('IRC: allowShutdown is deprecated: use authz instead')
        # ###

        if noticeOnChannel not in (True, False):
            config.error("noticeOnChannel must be boolean, not %r" %
                         (noticeOnChannel,))
        if useSSL:
            # SSL client needs a ClientContextFactory for some SSL mumbo-jumbo
            ssl.ensureHasSSL(self.__class__.__name__)
        if authz is not None:
            for acl in authz.values():
                if not isinstance(acl, (list, tuple, bool)):
                    config.error(
                        "authz values must be bool or a list of nicks")

        if generators is None:
            generators = self._create_default_generators()
        super().checkConfig(generators=generators, **kwargs)

    @defer.inlineCallbacks
    def reconfigService(self, host, nick, channels, pm_to_nicks=None, port=6667,
                        allowForce=None, tags=None, password=None, generators=None,
                        showBlameList=True, useRevisions=False,
                        useSSL=False, lostDelay=None, failedDelay=None, useColors=False,
                        allowShutdown=None, noticeOnChannel=False, authz=None, **kwargs
                        ):

        # need to stash these so we can detect changes later
        self.host = host
        self.port = port
        self.nick = nick
        self.join_channels = channels
        if pm_to_nicks is None:
            pm_to_nicks = []
        self.pm_to_nicks = pm_to_nicks
        self.password = password
        if authz is None:
            self.authz = {}
        else:
            self.authz = authz
        self.useRevisions = useRevisions
        self.tags = tags
        self.notify_events = {}
        self.noticeOnChannel = noticeOnChannel
        if generators is None:
            generators = self._create_default_generators()
        yield super().reconfigService(generators=generators, **kwargs)

        # deprecated...
        if allowForce is not None:
            self.authz[('force', 'stop')] = allowForce
        if allowShutdown is not None:
            self.authz[('shutdown')] = allowShutdown
        # ###
        # This function is only called in case of reconfig with changes
        # We don't try to be smart here. Just restart the bot if config has
        # changed.
        if self.f is not None:
            self.f.shutdown()
        self.f = IrcStatusFactory(self.nick, self.password,
                                  self.join_channels, self.pm_to_nicks,
                                  self.authz, self.tags,
                                  self.notify_events, parent=self,
                                  noticeOnChannel=noticeOnChannel,
                                  useRevisions=useRevisions,
                                  showBlameList=showBlameList,
                                  lostDelay=lostDelay,
                                  failedDelay=failedDelay,
                                  useColors=useColors
                                  )

        if useSSL:
            cf = ssl.ClientContextFactory()
            c = internet.SSLClient(self.host, self.port, self.f, cf)
        else:
            c = internet.TCPClient(self.host, self.port, self.f)

        c.setServiceParent(self)

    def _create_default_generators(self):
        formatter = MessageFormatterRenderable('Build done.')
        return [
            BuildStatusGenerator(
                message_formatter=formatter
            )
        ]
    #FIXME: add notice support
    def sendMessage(self, reports):
        body = reports[0].get('body', None)
        print(body)
        for c in self.join_channels:
            if isinstance(c, dict):
                channel = c.get('channel', None)
                print(channel)
                self.f.p.msg(channel, assembleFormattedText(A.normal[body]))
