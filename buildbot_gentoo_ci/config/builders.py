# Copyright 2020 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from buildbot.plugins import util
from buildbot_gentoo_ci.config import buildfactory

def gentoo_builders(b=[]):
    b.append(util.BuilderConfig(name='update_db_packages', workername='updatedb_1', factory=buildfactory.f_update_db_packages()))
    return b
