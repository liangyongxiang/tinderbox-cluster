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
# Origins: buildbot.config.py
# Modifyed by Gentoo Authors.
# Copyright 2021 Gentoo Authors

import datetime
import inspect
import os
import re
import sys
import traceback
import warnings
from types import MethodType

from twisted.python import failure
from twisted.python import log
from twisted.python.compat import execfile
from zope.interface import implementer

from buildbot import interfaces
from buildbot import locks
from buildbot import util
from buildbot.interfaces import IRenderable
from buildbot.revlinks import default_revlink_matcher
from buildbot.util import ComparableMixin
from buildbot.util import bytes2unicode
from buildbot.util import config as util_config
from buildbot.util import identifiers as util_identifiers
from buildbot.util import safeTranslate
from buildbot.util import service as util_service
from buildbot.warnings import ConfigWarning
from buildbot.warnings import warn_deprecated
from buildbot.config import ConfigErrors, error
from buildbot.config.master import loadConfigDict

_errors = None

DEFAULT_DB_URL = 'sqlite:///gentoo.sqlite'
DEFAULT_REPOSITORY_BASEDIR = '/srv/repository'

#Use GentooCiConfig.loadFromDict
@implementer(interfaces.IConfigLoader)
class FileLoader(ComparableMixin):
    compare_attrs = ['basedir', 'configFileName']

    def __init__(self, basedir, configFileName):
        self.basedir = basedir
        self.configFileName = configFileName

    def loadConfig(self):
        # from here on out we can batch errors together for the user's
        # convenience
        global _errors
        _errors = errors = ConfigErrors()

        try:
            filename, config_dict = loadConfigDict(
                self.basedir, self.configFileName)
            config = GentooCiConfig.loadFromDict(config_dict, filename)
        except ConfigErrors as e:
            errors.merge(e)
        finally:
            _errors = None

        if errors:
            raise errors

        return config

# Modifyed for Gentoo Ci settings
class GentooCiConfig(util.ComparableMixin):

    def __init__(self):
        self.db = dict(
            db_url=DEFAULT_DB_URL,
        )

    _known_config_keys = set([
        "db_url",
        "project",
        "repository_basedir"
    ])

    compare_attrs = list(_known_config_keys)

    @classmethod
    def loadFromDict(cls, config_dict, filename):
        # warning, all of this is loaded from a thread
        global _errors
        _errors = errors = ConfigErrors()

        # check for unknown keys
        unknown_keys = set(config_dict.keys()) - cls._known_config_keys
        if unknown_keys:
            if len(unknown_keys) == 1:
                error('Unknown BuildmasterConfig key {}'.format(unknown_keys.pop()))
            else:
                error('Unknown BuildmasterConfig keys {}'.format(', '.join(sorted(unknown_keys))))

        # instantiate a new config object, which will apply defaults
        # automatically
        config = cls()
        # and defer the rest to sub-functions, for code clarity
        try:
            config.load_db(config_dict)
            config.load_project(config_dict)
        finally:
            _errors = None

        if errors:
            raise errors

        return config

    @staticmethod
    def getDbUrlFromConfig(config_dict, throwErrors=True):

        # we don't attempt to parse db URLs here - the engine strategy will do
        # so.
        if 'db_url' in config_dict:
            return config_dict['db_url']

        return DEFAULT_DB_URL

    def load_db(self, config_dict):
        self.db = dict(db_url=self.getDbUrlFromConfig(config_dict))

    def load_project(self, config_dict):
        self.project = {}
        if 'project' in config_dict:
            self.project['project'] = config_dict['project']
        else:
            error("project are not configured")
        if 'repository_basedir' in config_dict:
            self.project['repository_basedir'] = config_dict['repository_basedir']
        else:
            self.project['repository_basedir'] = DEFAULT_REPOSITORY_BASEDIR
