# Copyright 2021 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from twisted.python import log
from twisted.internet import defer

from buildbot import config as master_config
from buildbot.db import exceptions
from buildbot.scripts.base import isBuildmasterDir
from buildbot.util.service import BuildbotService
from buildbot import version

from buildbot_gentoo_ci.db import connector as dbconnector
from buildbot_gentoo_ci.config import config

class GentooCiService(BuildbotService):

    name="gentooci"

    def checkConfig(self, basedir, **kwargs):
        self.basedir = basedir
        if not isBuildmasterDir(self.basedir):
            master_config.error("Can't find buildbot.tac in basedir")
            return

    @defer.inlineCallbacks
    def reconfigService(self, **kwargs):
        return defer.succeed(None)

    @defer.inlineCallbacks
    def startService(self):
        self.config_loader = config.FileLoader(self.basedir, 'gentooci.cfg')
        self.config = self.config_loader.loadConfig()
        self.db = dbconnector.DBConnector(self.basedir)
        yield self.db.setServiceParent(self)
        log.msg("Starting Gentoo-Ci Service -- buildbot.version: {}".format(version))
        # setup the db
        try:
            yield self.db.setup(self.config)
        except exceptions.DatabaseNotReadyError:
            # (message was already logged)
            self.master.reactor.stop()
            return
