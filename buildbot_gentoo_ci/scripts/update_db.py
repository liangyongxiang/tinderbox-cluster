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
# Origins: buildbot.scripts.base.py
#       buildbot.scripts.upgrade_master.py
# Modifyed by Gentoo Authors.
# Copyright 2020 Gentoo Authors

import os
import signal
import sys
import traceback

from twisted.internet import defer
from buildbot.master import BuildMaster
from buildbot.util import stripUrlPassword
from buildbot.config import ConfigErrors

from buildbot_gentoo_ci.db import connector
from buildbot_gentoo_ci.config.config import FileLoader

# Use FileLoader from Gentoo Ci 
def loadConfig(config, configFileName='master.cfg'):
    if not config['quiet']:
        print("checking {}".format(configFileName))

    try:
        master_cfg = FileLoader(
            config['basedir'], configFileName).loadConfig()
    except ConfigErrors as e:
        print("Errors loading configuration:")

        for msg in e.errors:
            print("  " + msg)
        return None
    except Exception:
        print("Errors loading configuration:")
        traceback.print_exc(file=sys.stdout)
        return None

    return master_cfg

#Use the db from Gentoo Ci
@defer.inlineCallbacks
def upgradeDatabase(config, master_cfg):
    if not config['quiet']:
        print("upgrading database ({})".format(stripUrlPassword(master_cfg.db['db_url'])))
        print("Warning: Stopping this process might cause data loss")

    def sighandler(signum, frame):
        msg = " ".join("""
        WARNING: ignoring signal {}.
        This process should not be interrupted to avoid database corruption.
        If you really need to terminate it, use SIGKILL.
        """.split())
        print(msg.format(signum))

    prev_handlers = {}
    try:
        for signame in ("SIGTERM", "SIGINT", "SIGQUIT", "SIGHUP",
                        "SIGUSR1", "SIGUSR2", "SIGBREAK"):
            if hasattr(signal, signame):
                signum = getattr(signal, signame)
                prev_handlers[signum] = signal.signal(signum, sighandler)

        master = BuildMaster(config['basedir'])
        master.config = master_cfg
        master.db.disownServiceParent()
        db = connector.DBConnector(basedir=config['basedir'])
        yield db.setServiceParent(master)
        yield db.setup(master_cfg, check_version=False, verbose=not config['quiet'])
        yield db.model.upgrade()
        yield db.masters.setAllMastersActiveLongTimeAgo()

    finally:
        # restore previous signal handlers
        for signum, handler in prev_handlers.items():
            signal.signal(signum, handler)

# Use gentooci.cfg for config
def upgradeGentooCi(config):
    master_cfg = loadConfig(config, 'gentooci.cfg')
    if not master_cfg:
        return defer.succeed(1)
    return _upgradeMaster(config, master_cfg)

# No changes
def _upgradeMaster(config, master_cfg):
    try:
        upgradeDatabase(config, master_cfg)
    except Exception:
        e = traceback.format_exc()
        print("problem while upgrading!:\n" + e, file=sys.stderr)
        return 1
    else:
        if not config['quiet']:
            print("upgrade complete")
    return 0
