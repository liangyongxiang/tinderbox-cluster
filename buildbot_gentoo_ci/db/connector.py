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
# Origins: buildbot.db.connector.py
# Modifyed by Gentoo Authors.
# Copyright 2021 Gentoo Authors

import textwrap

from twisted.application import internet
from twisted.internet import defer
from twisted.python import log

from buildbot import util
from buildbot.db import enginestrategy
from buildbot.db import exceptions
from buildbot.db import pool
from buildbot.util import service

from buildbot_gentoo_ci.db import model
from buildbot_gentoo_ci.db import projects
from buildbot_gentoo_ci.db import repositorys
from buildbot_gentoo_ci.db import categorys
from buildbot_gentoo_ci.db import packages
from buildbot_gentoo_ci.db import versions
from buildbot_gentoo_ci.db import keywords

upgrade_message = textwrap.dedent("""\

    The Buildmaster database needs to be upgraded before this version of
    buildbot can run.  Use the following command-line

        buildbot upgrade-master {basedir}

    to upgrade the database, and try starting the buildmaster again.  You may
    want to make a backup of your buildmaster before doing so.
    """).strip()

# Gentoo Ci tables and ConnectorComponent
class DBConnector(service.ReconfigurableServiceMixin,
                  service.AsyncMultiService):
    # The connection between Buildbot and its backend database.  This is
    # generally accessible as master.db, but is also used during upgrades.
    #
    # Most of the interesting operations available via the connector are
    # implemented in connector components, available as attributes of this
    # object, and listed below.

    # Period, in seconds, of the cleanup task.  This master will perform
    # periodic cleanup actions on this schedule.
    CLEANUP_PERIOD = 3600

    def __init__(self, basedir):
        super().__init__()
        self.setName('db')
        self.basedir = basedir

        # set up components
        self._engine = None  # set up in reconfigService
        self.pool = None  # set up in reconfigService

    @defer.inlineCallbacks
    def setServiceParent(self, p):
        yield super().setServiceParent(p)
        self.model = model.Model(self)
        self.projects = projects.ProjectsConnectorComponent(self)
        self.repositorys = repositorys.RepositorysConnectorComponent(self)
        self.categorys = categorys.CategorysConnectorComponent(self)
        self.packages = packages.PackagesConnectorComponent(self)
        self.versions = versions.VersionsConnectorComponent(self)
        self.keywords = keywords.KeywordsConnectorComponent(self)

    @defer.inlineCallbacks
    def setup(self, config, check_version=True, verbose=True):
        db_url = config.db['db_url']

        log.msg("Setting up database with URL %r"
                % util.stripUrlPassword(db_url))

        # set up the engine and pool
        self._engine = enginestrategy.create_engine(db_url,
                                                    basedir=self.basedir)
        self.pool = pool.DBThreadPool(
            self._engine, reactor=self.master.reactor, verbose=verbose)

        # make sure the db is up to date, unless specifically asked not to
        if check_version:
            if db_url == 'sqlite://':
                # Using in-memory database. Since it is reset after each process
                # restart, `buildbot upgrade-master` cannot be used (data is not
                # persistent). Upgrade model here to allow startup to continue.
                self.model.upgrade()
            current = yield self.model.is_current()
            if not current:
                for l in upgrade_message.format(basedir=self.basedir).split('\n'):
                    log.msg(l)
                raise exceptions.DatabaseNotReadyError()
